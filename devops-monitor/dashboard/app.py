"""Streamlit dashboard for the DevOps Monitoring API."""

import os
import time

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "dev-api-key")
MAX_HISTORY = 60


@st.cache_data(ttl=2)
def fetch_metrics() -> dict:
    """Fetch current system metrics from the API."""
    response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=5)
def fetch_servers() -> list[dict]:
    """Fetch the list of monitored servers."""
    response = requests.get(f"{API_BASE_URL}/servers", timeout=5)
    response.raise_for_status()
    return response.json()


def register_server(name: str, host: str, port: int) -> dict:
    """Register a new server via the API."""
    response = requests.post(
        f"{API_BASE_URL}/servers",
        json={"name": name, "host": host, "port": port},
        headers={"X-API-Key": API_KEY},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def trigger_health_check(server_id: str) -> dict:
    """Trigger an immediate health check for a server."""
    response = requests.post(
        f"{API_BASE_URL}/servers/{server_id}/check",
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def style_servers(df: pd.DataFrame):
    """Apply colour-coding based on server status."""

    def row_style(row: pd.Series) -> list[str]:
        colors = {
            "UP": "background-color: #90EE90",
            "DEGRADED": "background-color: #FFD700",
            "DOWN": "background-color: #FF6B6B",
        }
        color = colors.get(row["status"], "")
        return [color] * len(row)

    return df.style.apply(row_style, axis=1)


def _render_metrics_content(placeholder) -> None:
    """Update the metrics placeholder with the latest API data."""
    with placeholder.container():
        try:
            metrics = fetch_metrics()
        except requests.RequestException as exc:
            st.error(f"Unable to fetch metrics: {exc}")
            return

        col1, col2, col3 = st.columns(3)
        col1.metric("CPU %", f"{metrics['cpu_percent']:.1f}")
        col2.metric("Memory %", f"{metrics['memory_percent']:.1f}")
        col3.metric("Disk %", f"{metrics['disk_percent']:.1f}")

        history = st.session_state.metrics_history
        history.append(
            {
                "cpu_percent": metrics["cpu_percent"],
                "memory_percent": metrics["memory_percent"],
            }
        )
        st.session_state.metrics_history = history[-MAX_HISTORY:]

        if history:
            chart_df = pd.DataFrame(st.session_state.metrics_history)
            st.line_chart(chart_df)


def render_metrics_tab() -> None:
    """Display live system metrics and a CPU/memory chart."""
    if "metrics_history" not in st.session_state:
        st.session_state.metrics_history = []

    placeholder = st.empty()
    _render_metrics_content(placeholder)
    time.sleep(2)
    st.rerun()


def render_servers_tab() -> None:
    """Display servers and allow registration and health checks."""
    try:
        servers = fetch_servers()
    except requests.RequestException as exc:
        st.error(f"Unable to fetch servers: {exc}")
        return

    if servers:
        df = pd.DataFrame(servers)
        st.dataframe(style_servers(df), use_container_width=True)
    else:
        st.info("No servers registered yet.")

    st.subheader("Register a server")
    with st.form("register_server_form"):
        name = st.text_input("Name")
        host = st.text_input("Host", value="localhost")
        port = st.number_input("Port", min_value=1, max_value=65535, value=8000)
        submitted = st.form_submit_button("Add server")

    if submitted:
        try:
            created = register_server(name, host, int(port))
            fetch_servers.clear()
            st.success(f"Server '{created['name']}' registered.")
            st.rerun()
        except requests.RequestException as exc:
            st.error(f"Registration failed: {exc}")

    if servers:
        st.subheader("Health check")
        server_names = {f"{s['name']} ({s['host']}:{s['port']})": s["id"] for s in servers}
        selected_label = st.selectbox("Select a server", options=list(server_names.keys()))
        if st.button("Run health check"):
            server_id = server_names[selected_label]
            try:
                result = trigger_health_check(server_id)
                fetch_servers.clear()
                st.success(result["message"])
                time.sleep(1)
                st.rerun()
            except requests.RequestException as exc:
                st.error(f"Health check failed: {exc}")


def main() -> None:
    """Run the Streamlit dashboard."""
    st.set_page_config(page_title="DevOps Monitor", layout="wide")
    st.title("DevOps Monitoring Dashboard")

    metrics_tab, servers_tab = st.tabs(["Metrics", "Servers"])

    with servers_tab:
        render_servers_tab()

    with metrics_tab:
        render_metrics_tab()


if __name__ == "__main__":
    main()
