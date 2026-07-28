//! REST + WebSocket API for live sims and replay.

use axum::extract::ws::{Message, WebSocket, WebSocketUpgrade};
use axum::extract::{Path, State};
use axum::response::IntoResponse;
use axum::routing::{get, post};
use axum::{Json, Router};
use bace_core::{Action, Behavior, EndCondition, ScenarioConfig, Simulation};
use bace_record::{list_runs, load_episode, EpisodeMeta, EpisodeRecord};
use bace_vec::{ParallelEnvs, VecEnvConfig};
use dashmap::DashMap;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::Mutex;
use uuid::Uuid;

pub struct LiveJob {
    pub id: String,
    pub envs: Mutex<ParallelEnvs>,
    pub status: Mutex<String>,
}

pub struct AppState {
    pub runs_dir: PathBuf,
    pub jobs: DashMap<String, Arc<LiveJob>>,
}

impl AppState {
    pub fn new(runs_dir: PathBuf) -> Self {
        Self {
            runs_dir,
            jobs: DashMap::new(),
        }
    }
}

pub fn router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/runs", get(get_runs))
        .route("/runs/:id", get(get_run))
        .route("/jobs", get(list_jobs).post(create_job))
        .route("/jobs/:id", get(get_job))
        .route("/jobs/:id/step", post(step_job))
        .route("/jobs/:id/ws", get(job_ws))
        .route("/experiment", post(run_experiment_api))
        .with_state(state)
}

async fn health() -> Json<serde_json::Value> {
    Json(serde_json::json!({"ok": true, "version": "2.0.0"}))
}

async fn get_runs(State(state): State<Arc<AppState>>) -> Json<Vec<EpisodeMeta>> {
    Json(list_runs(&state.runs_dir).unwrap_or_default())
}

async fn get_run(
    State(state): State<Arc<AppState>>,
    Path(id): Path<String>,
) -> Result<Json<EpisodeRecord>, (axum::http::StatusCode, String)> {
    let path = state.runs_dir.join(&id);
    load_episode(path)
        .map(Json)
        .map_err(|e| (axum::http::StatusCode::NOT_FOUND, e.to_string()))
}

#[derive(Debug, Deserialize)]
pub struct CreateJobRequest {
    pub num_envs: Option<usize>,
    pub max_cycles: Option<u32>,
    pub record: Option<bool>,
    pub blue_behavior: Option<String>,
    pub red_behavior: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct JobInfo {
    pub id: String,
    pub num_envs: usize,
    pub status: String,
}

fn parse_behavior(s: &str) -> Behavior {
    match s {
        "external" => Behavior::External,
        "duck" => Behavior::Duck,
        _ => Behavior::Baseline1,
    }
}

async fn create_job(
    State(state): State<Arc<AppState>>,
    Json(req): Json<CreateJobRequest>,
) -> Json<JobInfo> {
    let mut scenario = ScenarioConfig::default();
    if let Some(m) = req.max_cycles {
        scenario.env.max_cycles = m;
    }
    if let Some(b) = &req.blue_behavior {
        scenario.blue.behavior = parse_behavior(b);
    } else {
        scenario.blue.behavior = Behavior::Baseline1;
    }
    if let Some(r) = &req.red_behavior {
        scenario.red.behavior = parse_behavior(r);
    }
    let num = req.num_envs.unwrap_or(4).clamp(1, 64);
    let cfg = VecEnvConfig {
        num_envs: num,
        scenario,
        record: req.record.unwrap_or(true),
        runs_dir: state.runs_dir.clone(),
    };
    let mut envs = ParallelEnvs::new(cfg);
    envs.reset_all(Some(1));
    let id = Uuid::new_v4().to_string();
    let job = Arc::new(LiveJob {
        id: id.clone(),
        envs: Mutex::new(envs),
        status: Mutex::new("running".into()),
    });
    state.jobs.insert(id.clone(), job);
    Json(JobInfo {
        id,
        num_envs: num,
        status: "running".into(),
    })
}

async fn list_jobs(State(state): State<Arc<AppState>>) -> Json<Vec<JobInfo>> {
    let mut out = Vec::new();
    for item in state.jobs.iter() {
        let status = item.status.lock().await.clone();
        out.push(JobInfo {
            id: item.id.clone(),
            num_envs: item.envs.lock().await.num_envs(),
            status,
        });
    }
    Json(out)
}

async fn get_job(
    State(state): State<Arc<AppState>>,
    Path(id): Path<String>,
) -> Result<Json<serde_json::Value>, (axum::http::StatusCode, String)> {
    let job = state
        .jobs
        .get(&id)
        .ok_or((axum::http::StatusCode::NOT_FOUND, "job not found".into()))?;
    let envs = job.envs.lock().await;
    let snaps = envs.snapshots();
    Ok(Json(serde_json::json!({
        "id": id,
        "status": *job.status.lock().await,
        "snapshots": snaps,
    })))
}

async fn step_job(
    State(state): State<Arc<AppState>>,
    Path(id): Path<String>,
) -> Result<Json<serde_json::Value>, (axum::http::StatusCode, String)> {
    let job = state
        .jobs
        .get(&id)
        .ok_or((axum::http::StatusCode::NOT_FOUND, "job not found".into()))?;
    let mut envs = job.envs.lock().await;
    let n = envs.num_envs();
    let actions: Vec<HashMap<String, Action>> = (0..n).map(|_| HashMap::new()).collect();
    let results = envs.step_all(&actions);
    let snaps = envs.snapshots();
    let all_done = snaps.iter().all(|s| s.end != EndCondition::Ongoing);
    if all_done {
        *job.status.lock().await = "finished".into();
        envs.finish_recordings();
    }
    Ok(Json(serde_json::json!({
        "results_end": results.iter().map(|r| format!("{:?}", r.end)).collect::<Vec<_>>(),
        "snapshots": snaps,
    })))
}

async fn job_ws(
    ws: WebSocketUpgrade,
    State(state): State<Arc<AppState>>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    ws.on_upgrade(move |socket| handle_ws(socket, state, id))
}

async fn handle_ws(mut socket: WebSocket, state: Arc<AppState>, id: String) {
    loop {
        let Some(job) = state.jobs.get(&id) else {
            break;
        };
        let payload = {
            let mut envs = job.envs.lock().await;
            let n = envs.num_envs();
            let actions: Vec<HashMap<String, Action>> = (0..n).map(|_| HashMap::new()).collect();
            let status = job.status.lock().await.clone();
            if status == "running" {
                envs.step_all(&actions);
            }
            let snaps = envs.snapshots();
            let all_done = snaps.iter().all(|s| s.end != EndCondition::Ongoing);
            if all_done && status == "running" {
                *job.status.lock().await = "finished".into();
                envs.finish_recordings();
            }
            serde_json::json!({
                "id": id,
                "status": *job.status.lock().await,
                "snapshots": snaps,
            })
        };
        if socket
            .send(Message::Text(payload.to_string()))
            .await
            .is_err()
        {
            break;
        }
        tokio::time::sleep(Duration::from_millis(100)).await;
    }
}

#[derive(Debug, Deserialize)]
pub struct ExperimentRequest {
    pub cases: usize,
    pub max_cycles: Option<u32>,
}

async fn run_experiment_api(Json(req): Json<ExperimentRequest>) -> Json<serde_json::Value> {
    let n = req.cases.clamp(1, 256);
    let mut cases = Vec::with_capacity(n);
    for i in 0..n {
        let mut cfg = ScenarioConfig::default();
        cfg.env.seed = i as u64 + 1;
        cfg.env.max_cycles = req.max_cycles.unwrap_or(200);
        cfg.blue.behavior = Behavior::Baseline1;
        cfg.red.behavior = Behavior::Duck;
        // vary d_shot slightly
        let d = 0.7 + (i as f64) * 0.01;
        cfg.blue.beh_config.d_shot = vec![d];
        cases.push(cfg);
    }
    let results = bace_vec::run_experiment(cases, 8);
    let wins = results
        .iter()
        .filter(|(_, e, _)| *e == EndCondition::RedKilled)
        .count();
    Json(serde_json::json!({
        "cases": results.len(),
        "red_killed": wins,
        "results": results.iter().map(|(c,e,s)| serde_json::json!({
            "seed": c.env.seed,
            "d_shot": c.blue.beh_config.d_shot,
            "end": format!("{:?}", e),
            "steps": s,
        })).collect::<Vec<_>>(),
    }))
}

#[allow(dead_code)]
fn _smoke_single() {
    let _ = Simulation::new(ScenarioConfig::default());
}
