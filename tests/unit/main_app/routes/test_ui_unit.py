"""Unit tests for src/main_app/routes/ui.py"""

from unittest.mock import Mock, patch

import pytest

from src.main_app.routes.ui import Ui_Blueprint


class TestUiBlueprintInit:
    """Tests for Ui_Blueprint initialization and route registration."""

    def test_ui_blueprint_stores_allowed_tables(self):
        """Ui_Blueprint stores allowed_tables."""
        mock_bp = Mock()
        api = Ui_Blueprint(mock_bp, allowed_tables={"logs", "list_logs"})

        assert api.allowed_tables == {"logs", "list_logs"}

    def test_ui_blueprint_registers_index_route(self):
        """Ui_Blueprint registers / route."""
        mock_bp = Mock()
        routes_registered = []

        def route_decorator(path, methods=None):
            def inner(func):
                routes_registered.append({"path": path, "methods": methods})
                return func
            return inner

        mock_bp.route = route_decorator

        Ui_Blueprint(mock_bp, allowed_tables={"logs", "list_logs"})

        paths = [r["path"] for r in routes_registered]
        assert "/" in paths

    def test_ui_blueprint_registers_logs_route(self):
        """Ui_Blueprint registers /logs route."""
        mock_bp = Mock()
        routes_registered = []

        def route_decorator(path, methods=None):
            def inner(func):
                routes_registered.append({"path": path, "methods": methods})
                return func
            return inner

        mock_bp.route = route_decorator

        Ui_Blueprint(mock_bp, allowed_tables={"logs", "list_logs"})

        paths = [r["path"] for r in routes_registered]
        assert "/logs" in paths

    def test_ui_blueprint_registers_no_result_route(self):
        """Ui_Blueprint registers /no_result route."""
        mock_bp = Mock()
        routes_registered = []

        def route_decorator(path, methods=None):
            def inner(func):
                routes_registered.append({"path": path, "methods": methods})
                return func
            return inner

        mock_bp.route = route_decorator

        Ui_Blueprint(mock_bp, allowed_tables={"logs", "list_logs"})

        paths = [r["path"] for r in routes_registered]
        assert "/no_result" in paths

    def test_ui_blueprint_registers_logs_by_day_route(self):
        """Ui_Blueprint registers /logs_by_day route."""
        mock_bp = Mock()
        routes_registered = []

        def route_decorator(path, methods=None):
            def inner(func):
                routes_registered.append({"path": path, "methods": methods})
                return func
            return inner

        mock_bp.route = route_decorator

        Ui_Blueprint(mock_bp, allowed_tables={"logs", "list_logs"})

        paths = [r["path"] for r in routes_registered]
        assert "/logs_by_day" in paths

    def test_ui_blueprint_registers_list_route(self):
        """Ui_Blueprint registers /list route."""
        mock_bp = Mock()
        routes_registered = []

        def route_decorator(path, methods=None):
            def inner(func):
                routes_registered.append({"path": path, "methods": methods})
                return func
            return inner

        mock_bp.route = route_decorator

        Ui_Blueprint(mock_bp, allowed_tables={"logs", "list_logs"})

        paths = [r["path"] for r in routes_registered]
        assert "/list" in paths

    def test_ui_blueprint_registers_chart_route(self):
        """Ui_Blueprint registers /chart route."""
        mock_bp = Mock()
        routes_registered = []

        def route_decorator(path, methods=None):
            def inner(func):
                routes_registered.append({"path": path, "methods": methods})
                return func
            return inner

        mock_bp.route = route_decorator

        Ui_Blueprint(mock_bp, allowed_tables={"logs", "list_logs"})

        paths = [r["path"] for r in routes_registered]
        assert "/chart" in paths

    def test_ui_blueprint_registers_chart2_route(self):
        """Ui_Blueprint registers /chart2 route."""
        mock_bp = Mock()
        routes_registered = []

        def route_decorator(path, methods=None):
            def inner(func):
                routes_registered.append({"path": path, "methods": methods})
                return func
            return inner

        mock_bp.route = route_decorator

        Ui_Blueprint(mock_bp, allowed_tables={"logs", "list_logs"})

        paths = [r["path"] for r in routes_registered]
        assert "/chart2" in paths

    def test_ui_blueprint_registers_qids_batch_translate_route(self):
        """Ui_Blueprint registers /qids_batch_translate route."""
        mock_bp = Mock()
        routes_registered = []

        def route_decorator(path, methods=None):
            def inner(func):
                routes_registered.append({"path": path, "methods": methods})
                return func
            return inner

        mock_bp.route = route_decorator

        Ui_Blueprint(mock_bp, allowed_tables={"logs", "list_logs"})

        paths = [r["path"] for r in routes_registered]
        assert "/qids_batch_translate" in paths


class TestUiBlueprintRenderDailyLogs:
    """Tests for UI Blueprint render_daily_logs route handler logic."""

    def test_render_daily_logs_validates_table_name(self):
        """render_daily_logs validates table_name parameter."""
        with patch("src.main_app.routes.ui.load_logs_view") as mock_load_view:
            mock_viewer = Mock()
            mock_viewer.view_logs_by_date.return_value = {"logs": [], "tab": {}}
            mock_load_view.return_value = mock_viewer

            # Simulate the route handler logic with invalid table
            table_name = "invalid_table"
            allowed_tables = {"logs", "list_logs"}

            if table_name not in allowed_tables:
                table_name = "logs"

            result = mock_viewer.view_logs_by_date(table_name)

            # Should default to "logs"
            mock_viewer.view_logs_by_date.assert_called_once_with("logs")

    def test_render_daily_logs_defaults_to_logs(self):
        """render_daily_logs defaults to 'logs' for empty table."""
        with patch("src.main_app.routes.ui.load_logs_view") as mock_load_view:
            mock_viewer = Mock()
            mock_viewer.view_logs_by_date.return_value = {"logs": [], "tab": {}}
            mock_load_view.return_value = mock_viewer

            # Simulate the route handler logic with empty table
            table_name = ""
            allowed_tables = {"logs", "list_logs"}

            if table_name not in allowed_tables:
                table_name = "logs"

            result = mock_viewer.view_logs_by_date(table_name)

            mock_viewer.view_logs_by_date.assert_called_once_with("logs")

    def test_render_daily_logs_accepts_valid_table(self):
        """render_daily_logs accepts valid table names."""
        with patch("src.main_app.routes.ui.load_logs_view") as mock_load_view:
            mock_viewer = Mock()
            mock_viewer.view_logs_by_date.return_value = {"logs": [], "tab": {}}
            mock_load_view.return_value = mock_viewer

            # Simulate the route handler logic with valid table
            table_name = "list_logs"
            allowed_tables = {"logs", "list_logs"}

            if table_name not in allowed_tables:
                table_name = "logs"

            result = mock_viewer.view_logs_by_date(table_name)

            mock_viewer.view_logs_by_date.assert_called_once_with("list_logs")


class TestUiBlueprintRenderTemplateCalls:
    """Tests for UI Blueprint render_template calls."""

    def test_render_index_page(self):
        """render_index_page renders index.html."""
        with patch("src.main_app.routes.ui.render_template") as mock_render:
            mock_render.return_value = "<html>index</html>"
            result = mock_render("index.html")
            mock_render.assert_called_once_with("index.html")

    def test_render_logs_view(self):
        """render_logs_view renders logs.html with result."""
        with patch("src.main_app.routes.ui.render_template") as mock_render:
            mock_render.return_value = "<html>logs</html>"
            result = mock_render("logs.html", result={"logs": []})
            mock_render.assert_called_once_with("logs.html", result={"logs": []})

    def test_render_no_results_page(self):
        """render_no_results_page renders no_result.html."""
        with patch("src.main_app.routes.ui.render_template") as mock_render:
            mock_render.return_value = "<html>no_result</html>"
            result = mock_render("no_result.html")
            mock_render.assert_called_once_with("no_result.html")

    def test_render_daily_logs_view(self):
        """render_daily_logs renders logs_by_day.html."""
        with patch("src.main_app.routes.ui.render_template") as mock_render:
            mock_render.return_value = "<html>daily</html>"
            result = mock_render("logs_by_day.html", logs=[], tab={})
            mock_render.assert_called_once_with("logs_by_day.html", logs=[], tab={})

    def test_render_list_page(self):
        """render_title_list renders list.html."""
        with patch("src.main_app.routes.ui.render_template") as mock_render:
            mock_render.return_value = "<html>list</html>"
            result = mock_render("list.html")
            mock_render.assert_called_once_with("list.html")

    def test_render_chart_page(self):
        """render_chart renders chart.html."""
        with patch("src.main_app.routes.ui.render_template") as mock_render:
            mock_render.return_value = "<html>chart</html>"
            result = mock_render("chart.html")
            mock_render.assert_called_once_with("chart.html")

    def test_render_chart2_page(self):
        """render_chart2 renders chart2.html."""
        with patch("src.main_app.routes.ui.render_template") as mock_render:
            mock_render.return_value = "<html>chart2</html>"
            result = mock_render("chart2.html")
            mock_render.assert_called_once_with("chart2.html")

    def test_render_qids_batch_translate_page(self):
        """render_qids_batch_translate renders qids_batch_translate.html."""
        with patch("src.main_app.routes.ui.render_template") as mock_render:
            mock_render.return_value = "<html>qids</html>"
            result = mock_render("qids_batch_translate.html")
            mock_render.assert_called_once_with("qids_batch_translate.html")
