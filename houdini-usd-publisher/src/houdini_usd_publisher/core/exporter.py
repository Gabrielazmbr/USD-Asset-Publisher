from pathlib import Path

from houdini_usd_publisher.core.config import PublishConfig


class ExportError(Exception):
    pass


class USDExporter:
    def __init__(self, config: PublishConfig):
        self.config = config

    def export(self, lop_node_path: str, output_path: str | Path) -> Path:
        if not lop_node_path or not lop_node_path.startswith("/"):
            raise ExportError(f"LOP node not found: {lop_node_path}")

        import hou

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        lop_node = hou.node(lop_node_path)
        if lop_node is None:
            raise ExportError(f"LOP node not found: {lop_node_path}")

        out_context = hou.node("/out")
        rop = out_context.createNode("usd", "publisher_export_tmp")

        try:
            rop.parm("loppath").set(lop_node_path)
            rop.parm("lopoutput").set(str(output))
            rop.parm("execute").pressButton()
        except hou.Error as e:
            raise ExportError(f"Houdini export failed: {e}") from e
        finally:
            rop.destroy()

        if not output.exists():
            raise ExportError(f"File was not written: {output}")

        return output
