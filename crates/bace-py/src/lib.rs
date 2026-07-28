//! Python bindings for B-ACE 2.0 (PyO3).
//! Built with maturin; the pure-Python PettingZoo wrapper lives in `python/bace`.

use bace_core::{Action, ScenarioConfig, Simulation};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::collections::HashMap;

#[pyclass]
struct NativeEnv {
    sim: Simulation,
}

#[pymethods]
impl NativeEnv {
    #[new]
    #[pyo3(signature = (config_json=None))]
    fn new(config_json: Option<&str>) -> PyResult<Self> {
        let mut cfg = ScenarioConfig::default();
        if let Some(s) = config_json {
            cfg.merge_json(s).map_err(|e| {
                pyo3::exceptions::PyValueError::new_err(format!("config error: {e}"))
            })?;
        }
        Ok(Self {
            sim: Simulation::new(cfg),
        })
    }

    #[pyo3(signature = (seed=None))]
    fn reset(&mut self, seed: Option<u64>) -> PyResult<PyObject> {
        let result = self.sim.reset(seed);
        Python::with_gil(|py| step_to_py(py, &result))
    }

    fn step(&mut self, actions: Bound<'_, PyDict>) -> PyResult<PyObject> {
        let mut map = HashMap::new();
        for (k, v) in actions.iter() {
            let name: String = k.extract()?;
            let arr: Vec<f64> = v.extract()?;
            map.insert(name, Action::from_slice(&arr));
        }
        let result = self.sim.step(&map);
        Python::with_gil(|py| step_to_py(py, &result))
    }

    fn obs_size(&self) -> usize {
        self.sim.obs_size()
    }

    fn agent_ids(&self) -> Vec<String> {
        self.sim.blue_agent_ids.clone()
    }

    fn snapshot_json(&self) -> PyResult<String> {
        serde_json::to_string(&self.sim.snapshot())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    fn config_json(&self) -> PyResult<String> {
        self.sim
            .config
            .to_json_pretty()
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
}

fn step_to_py(py: Python<'_>, result: &bace_core::StepResult) -> PyResult<PyObject> {
    let obs = PyDict::new_bound(py);
    let rewards = PyDict::new_bound(py);
    let terms = PyDict::new_bound(py);
    let truncs = PyDict::new_bound(py);
    let infos = PyDict::new_bound(py);
    for (k, v) in &result.agents {
        obs.set_item(k, PyList::new_bound(py, &v.flat_obs))?;
        rewards.set_item(k, v.reward)?;
        terms.set_item(k, v.terminated)?;
        truncs.set_item(k, v.truncated)?;
        let info = PyDict::new_bound(py);
        info.set_item(
            "reward_breakdown",
            serde_json::to_string(&v.reward_breakdown).unwrap_or_default(),
        )?;
        infos.set_item(k, info)?;
    }
    let out = PyDict::new_bound(py);
    out.set_item("obs", obs)?;
    out.set_item("rewards", rewards)?;
    out.set_item("terminations", terms)?;
    out.set_item("truncations", truncs)?;
    out.set_item("infos", infos)?;
    out.set_item("end", format!("{:?}", result.end))?;
    out.set_item("action_step", result.action_step)?;
    Ok(out.into())
}

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<NativeEnv>()?;
    m.add("__version__", "2.0.0")?;
    Ok(())
}
