//! Episode trajectory recording for B-ACE 2.0.

use bace_core::{Action, EndCondition, RewardBreakdown, ScenarioConfig, SimSnapshot, StructuredObs};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fs::{self, File};
use std::io::{BufReader, BufWriter, Write};
use std::path::{Path, PathBuf};
use thiserror::Error;
use uuid::Uuid;

#[derive(Debug, Error)]
pub enum RecordError {
    #[error("io: {0}")]
    Io(#[from] std::io::Error),
    #[error("json: {0}")]
    Json(#[from] serde_json::Error),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StepRecord {
    pub action_step: u32,
    pub actions: std::collections::HashMap<String, Action>,
    pub rewards: std::collections::HashMap<String, f64>,
    pub reward_breakdowns: std::collections::HashMap<String, RewardBreakdown>,
    pub obs: std::collections::HashMap<String, StructuredObs>,
    pub snapshot: SimSnapshot,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EpisodeMeta {
    pub run_id: String,
    pub created_at: DateTime<Utc>,
    pub config: ScenarioConfig,
    pub end: EndCondition,
    pub total_steps: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EpisodeRecord {
    pub meta: EpisodeMeta,
    pub steps: Vec<StepRecord>,
}

pub struct Recorder {
    pub run_id: String,
    pub root: PathBuf,
    config: ScenarioConfig,
    steps: Vec<StepRecord>,
}

impl Recorder {
    pub fn new(root: impl AsRef<Path>, config: ScenarioConfig) -> Result<Self, RecordError> {
        let run_id = Uuid::new_v4().to_string();
        let dir = root.as_ref().join(&run_id);
        fs::create_dir_all(&dir)?;
        Ok(Self {
            run_id,
            root: dir,
            config,
            steps: Vec::new(),
        })
    }

    pub fn push(&mut self, step: StepRecord) {
        self.steps.push(step);
    }

    pub fn finish(self, end: EndCondition) -> Result<EpisodeRecord, RecordError> {
        let meta = EpisodeMeta {
            run_id: self.run_id.clone(),
            created_at: Utc::now(),
            config: self.config,
            end,
            total_steps: self.steps.len() as u32,
        };
        let rec = EpisodeRecord {
            meta,
            steps: self.steps,
        };
        let path = self.root.join("episode.json");
        let file = File::create(path)?;
        let mut w = BufWriter::new(file);
        serde_json::to_writer_pretty(&mut w, &rec)?;
        w.flush()?;
        let meta_path = self.root.join("meta.json");
        serde_json::to_writer_pretty(File::create(meta_path)?, &rec.meta)?;
        Ok(rec)
    }
}

pub fn load_episode(path: impl AsRef<Path>) -> Result<EpisodeRecord, RecordError> {
    let p = path.as_ref();
    let file_path = if p.is_dir() {
        p.join("episode.json")
    } else {
        p.to_path_buf()
    };
    let f = File::open(file_path)?;
    Ok(serde_json::from_reader(BufReader::new(f))?)
}

pub fn list_runs(root: impl AsRef<Path>) -> Result<Vec<EpisodeMeta>, RecordError> {
    let mut out = Vec::new();
    let root = root.as_ref();
    if !root.exists() {
        return Ok(out);
    }
    for entry in fs::read_dir(root)? {
        let entry = entry?;
        let meta_path = entry.path().join("meta.json");
        if meta_path.exists() {
            let meta: EpisodeMeta = serde_json::from_reader(BufReader::new(File::open(meta_path)?))?;
            out.push(meta);
        }
    }
    out.sort_by(|a, b| b.created_at.cmp(&a.created_at));
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use bace_core::ScenarioConfig;

    #[test]
    fn write_and_load() {
        let dir = std::env::temp_dir().join(format!("bace_rec_{}", Uuid::new_v4()));
        fs::create_dir_all(&dir).unwrap();
        let cfg = ScenarioConfig::default();
        let mut rec = Recorder::new(&dir, cfg).unwrap();
        let run_dir = rec.root.clone();
        rec.finish(EndCondition::MaxCycles).unwrap();
        let loaded = load_episode(&run_dir).unwrap();
        assert_eq!(loaded.meta.end, EndCondition::MaxCycles);
        fs::remove_dir_all(&dir).ok();
    }
}
