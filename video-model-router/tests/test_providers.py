import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from providers import PROVIDERS
from providers.base import VideoRequest


class AggregatedProviderTests(unittest.TestCase):
    def test_agnes_supports_12_seconds(self):
        p = PROVIDERS["agnes"]
        req = VideoRequest(provider="agnes", prompt="rainy city", duration=12)
        self.assertEqual(p.validate(req), [])
        _, body = p.build_create_request(req)
        self.assertEqual(body["seconds"], "12")
        self.assertEqual(body["size"], "720P")
        self.assertEqual(body["mode"], "text")

    def test_agnes_rejects_13_seconds(self):
        p = PROVIDERS["agnes"]
        errors = p.validate(VideoRequest(provider="agnes", prompt="x", duration=13))
        self.assertTrue(any("duration" in e for e in errors))

    def test_agnes_requires_public_urls(self):
        p = PROVIDERS["agnes"]
        errors = p.validate(VideoRequest(provider="agnes", prompt="x", first_frame="/tmp/a.png"))
        self.assertTrue(any("publicly reachable" in e for e in errors))

    def test_agnes_rejects_video_reference(self):
        p = PROVIDERS["agnes"]
        req = VideoRequest(provider="agnes", prompt="x", reference_videos=["https://example.com/a.mp4"])
        errors = p.validate(req)
        self.assertTrue(any("does not support reference videos" in e for e in errors))

    def test_agnes_limits_images_to_five(self):
        p = PROVIDERS["agnes"]
        req = VideoRequest(provider="agnes", prompt="x", reference_images=[f"https://example.com/{i}.png" for i in range(6)])
        errors = p.validate(req)
        self.assertTrue(any("too many reference images" in e for e in errors))

    def test_agnes_keyframe_body(self):
        p = PROVIDERS["agnes"]
        req = VideoRequest(provider="agnes", prompt="x", mode="keyframe", duration=6, first_frame="https://example.com/a.png", last_frame="https://example.com/b.png")
        self.assertEqual(p.validate(req), [])
        _, body = p.build_create_request(req)
        self.assertEqual(body["mode"], "keyframe")
        self.assertEqual(body["first_frame"], "https://example.com/a.png")
        self.assertEqual(body["last_frame"], "https://example.com/b.png")

    def test_seedance_still_available(self):
        p = PROVIDERS["seedance"]
        req = VideoRequest(provider="seedance", prompt="x", duration=8)
        self.assertEqual(p.validate(req), [])
        _, body = p.build_create_request(req)
        self.assertEqual(body["duration"], 8)
        self.assertEqual(body["model"], p.capabilities.default_model)


if __name__ == "__main__":
    unittest.main()


class DocumentationBoundaryTests(unittest.TestCase):
    def test_shared_references_exist_and_are_linked(self):
        root = Path(__file__).resolve().parents[1]
        refs = root / "references"
        required = [
            "README.md",
            "cinematography.md",
            "styles-and-visuals.md",
            "prompt-patterns.md",
            "continuity-and-transitions.md",
            "provider-profiles.md",
            "scene-recipes.md",
            "provider-contract.md",
        ]
        for name in required:
            path = refs / name
            self.assertTrue(path.is_file(), name)
            self.assertGreater(path.stat().st_size, 500, name)
        skill = (root / "SKILL.md").read_text(encoding="utf-8")
        for name in required:
            if name != "README.md":
                self.assertIn(name, skill)

    def test_seedance_supplement_does_not_duplicate_generic_vocabulary(self):
        # In the combined workspace this guards against vocabulary drift.
        # When the skill is published standalone, the sibling skill is absent.
        root = Path(__file__).resolve().parents[2]
        seed_path = root / "seedance2-skill" / "reference.md"
        if not seed_path.is_file():
            self.skipTest("seedance2-skill is not installed in this repository")
        seed = seed_path.read_text(encoding="utf-8")
        self.assertNotIn("## 镜头语言词汇库", seed)
        self.assertNotIn("## 风格词汇库", seed)
        self.assertIn("video-model-router/references/README.md", seed)
