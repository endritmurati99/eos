#!/usr/bin/env python3
from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.gateways.tts_local import synthesize_with_piper  # noqa: E402
from src.gateways.tts_pipeline import synthesize_briefing_audio  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fake_piper = tmp_path / "piper"
        fake_model = tmp_path / "voice.onnx"
        fake_config = tmp_path / "voice.onnx.json"
        output_dir = tmp_path / "out"

        fake_model.write_text("model", encoding="utf-8")
        fake_config.write_text("{}", encoding="utf-8")
        fake_piper.write_text(
            """#!/usr/bin/env python3
from pathlib import Path
import sys

args = sys.argv
output_path = Path(args[args.index("--output_file") + 1])
text = sys.stdin.read()
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_bytes(b"RIFF" + text.encode("utf-8"))
""",
            encoding="utf-8",
        )
        fake_piper.chmod(fake_piper.stat().st_mode | stat.S_IXUSR)

        result = synthesize_with_piper(
            "Guten Morgen. Dies ist ein kurzer Test.",
            piper_bin=fake_piper,
            model_path=fake_model,
            config_path=fake_config,
            vendor_path=tmp_path,
            output_dir=output_dir,
        )
        assert result["status"] == "success"
        assert result["provider"] == "piper_local"
        assert result["mime_type"] == "audio/wav"
        assert Path(result["audio_path"]).exists()
        assert result["duration_estimate"] > 0

        missing = synthesize_with_piper(
            "Hallo",
            piper_bin=tmp_path / "missing-piper",
            model_path=fake_model,
            config_path=fake_config,
            vendor_path=tmp_path,
            output_dir=output_dir,
        )
        assert missing["status"] == "config_missing"

    briefing_text = "### Heute steht an\n- Keine harten Termine bestaetigt."

    def failing_provider(**kwargs: Any) -> dict[str, Any]:
        return {
            "status": "provider_error",
            "provider": "mock",
            "audio_path": None,
            "mime_type": None,
            "duration_estimate": None,
            "error": "Audio delivery failed",
        }

    failed_audio = synthesize_briefing_audio(briefing_text, provider=failing_provider)
    assert failed_audio["status"] == "provider_error"
    assert "Audio delivery failed" not in briefing_text

    os.environ.pop("PYTHONPATH", None)
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
