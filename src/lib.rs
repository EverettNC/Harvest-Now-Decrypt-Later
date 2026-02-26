use pyo3::prelude::*;

/// This is our first Rust function that Python will be able to call!
#[pyfunction]
fn rust_engine_status() -> PyResult<String> {
    Ok("The Christman AI Project: Constant-time Rust backend is ONLINE.".to_string())
}

/// A Python module implemented in Rust.
#[pymodule]
fn christman_pq_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rust_engine_status, m)?)?;
    Ok(())
}
