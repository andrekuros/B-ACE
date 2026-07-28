//! B-ACE 2.0 dashboard HTTP/WebSocket server.

mod api;

use anyhow::Result;
use axum::Router;
use clap::Parser;
use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::Arc;
use tower_http::cors::CorsLayer;
use tower_http::services::ServeDir;
use tower_http::trace::TraceLayer;
use tracing_subscriber::EnvFilter;

use api::AppState;

#[derive(Parser, Debug)]
#[command(name = "bace-server", about = "B-ACE 2.0 web dashboard")]
struct Args {
    #[arg(long, default_value = "8787")]
    port: u16,
    #[arg(long, default_value = "runs")]
    runs_dir: PathBuf,
    #[arg(long, default_value = "web/dist")]
    static_dir: PathBuf,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("info".parse()?))
        .init();

    let args = Args::parse();
    std::fs::create_dir_all(&args.runs_dir)?;

    let state = Arc::new(AppState::new(args.runs_dir.clone()));
    let api = api::router(state);

    let app = Router::new()
        .nest("/api", api)
        .fallback_service(ServeDir::new(&args.static_dir))
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http());

    let addr = SocketAddr::from(([0, 0, 0, 0], args.port));
    tracing::info!("B-ACE 2.0 dashboard at http://{addr}");
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
}
