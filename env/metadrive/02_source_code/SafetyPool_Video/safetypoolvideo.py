#!/usr/bin/env python3
"""Build a synchronized MetaDrive comparison with termination-aware labels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


METHODS = ("SafetyPool", "Epsilon-Greedy", "NoisyNet", "RND")
INDIVIDUAL_ORDER = ("Epsilon-Greedy", "NoisyNet", "RND", "SafetyPool")
TILE_PLAY_ORDER = (
    (0, "Epsilon-Greedy"),
    (2, "RND"),
    (1, "NoisyNet"),
    (3, "SafetyPool"),
)
DISPLAY_LABELS = {
    "Epsilon-Greedy": "Car 1 - Epsilon-Greedy",
    "NoisyNet": "Car 3 - NoisyNet",
    "RND": "Car 2 - RND",
    "SafetyPool": "Car 4 - SafetyPool",
}
TELEMETRY_CLEARANCE = 58
RIGHT_COLUMN_BADGE_INSET = 180
BADGE_SAFE_MARGIN = 24
TILE_HEADER_HEIGHT = 76


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, default=Path("videos/comparison"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("videos/MetaDrive_comparison_status.mp4"),
    )
    parser.add_argument("--fps", type=int, default=20)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--title-seconds", type=float, default=2.0)
    parser.add_argument("--overall-title-seconds", type=float, default=2.0)
    parser.add_argument(
        "--transition-pause-seconds",
        type=float,
        default=0.0,
        help=(
            "Hold each seed's final comparison frame for this many seconds "
            "before the next seed."
        ),
    )
    parser.add_argument(
        "--individual-seconds",
        type=float,
        default=2.0,
        help=(
            "Before the four-panel comparison, show each policy individually "
            "for this many seconds in Epsilon, NoisyNet, RND, SafetyPool order."
        ),
    )
    parser.add_argument(
        "--individual-zoom",
        type=float,
        default=1.18,
        help="Road-focused crop enlargement for individual clips (default: 1.18).",
    )
    parser.add_argument("--tile-seconds", type=float, default=6.0)
    parser.add_argument("--seed19-safetypool-seconds", type=float, default=4.0)
    parser.add_argument("--tile-gap-seconds", type=float, default=2.0)
    parser.add_argument("--seed-gap-seconds", type=float, default=2.0)
    parser.add_argument(
        "--seed19-safetypool-video",
        type=Path,
        default=None,
        help="Optional extracted four-second SafetyPool-only video for seed 19.",
    )
    parser.add_argument(
        "--seed-duration",
        action="append",
        default=[],
        metavar="SEED=SECONDS",
        help=(
            "Limit a seed's comparison footage to a duration, for example "
            "--seed-duration 19=4. May be supplied more than once."
        ),
    )
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    return parser.parse_args()


def font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def title_card(width: int, height: int, seed: int) -> np.ndarray:
    image = Image.new("RGB", (width, height), "#166534")
    draw = ImageDraw.Draw(image)
    heading = "MetaDrive Frozen-Policy Comparison"
    seed_line = f"Training Seed {seed}"
    subtitle = "Same deterministic test episode and scenario for all four methods"
    heading_font = font(max(30, width // 31))
    seed_font = font(max(24, width // 42))
    subtitle_font = font(max(16, width // 58))
    box = draw.textbbox((0, 0), heading, font=heading_font)
    draw.text(
        ((width - (box[2] - box[0])) / 2, height * 0.31),
        heading,
        fill="white",
        font=heading_font,
    )
    box = draw.textbbox((0, 0), seed_line, font=seed_font)
    draw.text(
        ((width - (box[2] - box[0])) / 2, height * 0.44),
        seed_line,
        fill="white",
        font=seed_font,
    )
    box = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    draw.text(
        ((width - (box[2] - box[0])) / 2, height * 0.56),
        subtitle,
        fill="white",
        font=subtitle_font,
    )
    return np.asarray(image)


def overall_title_card(width: int, height: int, seeds: list[int]) -> np.ndarray:
    image = Image.new("RGB", (width, height), "#166534")
    draw = ImageDraw.Draw(image)
    text = "SafetyPool Testing"
    text_font = font(max(46, width // 18))
    box = draw.textbbox((0, 0), text, font=text_font)
    text_width = box[2] - box[0]
    text_height = box[3] - box[1]
    draw.text(
        ((width - text_width) / 2, (height - text_height) / 2 - box[1]),
        text,
        fill="white",
        font=text_font,
    )
    return np.asarray(image)


def read_status(video_path: Path) -> str | None:
    """Return an evidence-backed terminal label from recorder metadata."""
    metadata_path = video_path.with_suffix(".json")
    if not metadata_path.is_file():
        return None
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    termination = str(
        metadata.get("termination")
        or metadata.get("termination_reason")
        or ""
    ).strip().lower()
    if "collision" in termination or termination in {
        "crash",
        "crash_vehicle",
        "vehicle_collision",
    }:
        return "COLLISION"
    if termination in {"out_of_road", "out-of-road", "off_road", "off-road"}:
        return "OUT OF ROAD"
    return None


def panel(
    frame: np.ndarray,
    label: str,
    width: int,
    height: int,
    ended: bool,
    status: str | None,
) -> Image.Image:
    cleaned_frame = frame[:, :, :3].copy()
    source_height, source_width = cleaned_frame.shape[:2]
    # Step/Speed/Distance is permanently baked into the recorder's
    # upper-left corner. Remove that source region before any crop or resize
    # so the detector cannot mistake telemetry text for road content.
    telemetry_height = min(130, max(45, source_height // 3))
    telemetry_width = min(320, max(140, source_width // 2))
    cleaned_frame[:telemetry_height, :telemetry_width] = 255
    image = Image.fromarray(cleaned_frame).convert("RGB")
    canvas = Image.new("RGB", (width, height), "white")

    # Detect road/vehicle pixels, discard unused white margins, enlarge the
    # useful scene, and center it in the area below the fixed title header.
    pixels = np.asarray(image)
    minimum = pixels.min(axis=2)
    maximum = pixels.max(axis=2)
    content_mask = (minimum < 242) & (maximum > 35)
    content_mask[: min(70, image.height), :] = False
    ys, xs = np.where(content_mask)
    if len(xs) >= 20:
        left = max(0, int(xs.min()) - 24)
        right = min(image.width, int(xs.max()) + 25)
        top = max(0, int(ys.min()) - 24)
        bottom = min(image.height, int(ys.max()) + 25)
        image = image.crop((left, top, right, bottom))

    available_height = height - TILE_HEADER_HEIGHT
    # Fit the complete detected scene first so no vehicle is cropped out,
    # then apply the same modest 12% enlargement to every policy and seed.
    width_scale = (width * 0.88) / max(1, image.width)
    height_scale = (available_height * 0.88) / max(1, image.height)
    scale = min(width_scale, height_scale) * 1.12
    resized_width = max(1, round(image.width * scale))
    resized_height = max(1, round(image.height * scale))
    image = image.resize(
        (resized_width, resized_height),
        Image.Resampling.LANCZOS,
    )
    paste_x = (width - resized_width) // 2
    paste_y = TILE_HEADER_HEIGHT + (available_height - resized_height) // 2
    canvas.paste(image, (paste_x, paste_y))

    draw = ImageDraw.Draw(canvas, "RGBA")
    # Recorder telemetry is baked into the source frames. A uniform opaque
    # header removes it and guarantees identical annotation placement.
    draw.rectangle((0, 0, width, TILE_HEADER_HEIGHT), fill=(255, 255, 255, 255))

    # The recorder already writes Step/Speed/Distance in the upper-left.
    # Leave those pixels untouched and place the method label below them in
    # unused white space, using the same compact badge style as termination.
    label_font = font(max(13, width // 40))
    label_box = draw.textbbox((0, 0), label, font=label_font)
    label_width = label_box[2] - label_box[0] + 16
    label_height = label_box[3] - label_box[1] + 10
    # Center every policy title in the fixed white header.
    label_x = (width - label_width) // 2
    label_x = max(
        BADGE_SAFE_MARGIN,
        min(label_x, width - label_width - BADGE_SAFE_MARGIN),
    )
    label_y = 8
    label_fill = (
        (22, 101, 52, 230)
        if "SafetyPool" in label
        else (55, 65, 81, 225)
    )
    draw.rounded_rectangle(
        (
            label_x,
            label_y,
            label_x + label_width,
            label_y + label_height,
        ),
        radius=5,
        fill=label_fill,
        outline=(255, 255, 255, 230),
        width=1,
    )
    draw.text(
        (label_x + 8, label_y + 5 - label_box[1]),
        label,
        fill="white",
        font=label_font,
    )

    if ended and status is not None:
        # Put termination immediately below its policy name.
        status_font = font(max(13, width // 40))
        box = draw.textbbox((0, 0), status, font=status_font)
        text_width = box[2] - box[0]
        text_height = box[3] - box[1]
        pad_x, pad_y = 8, 5
        badge_width = text_width + 2 * pad_x
        badge_height = text_height + 2 * pad_y
        x = (width - badge_width) // 2
        x = max(
            BADGE_SAFE_MARGIN,
            min(x, width - badge_width - BADGE_SAFE_MARGIN),
        )
        y = label_y + label_height + 6
        fill = (
            (153, 27, 27, 230)
            if status == "COLLISION"
            else (161, 98, 7, 230)
        )
        draw.rounded_rectangle(
            (x, y, x + badge_width, y + badge_height),
            radius=5,
            fill=fill,
            outline=(255, 255, 255, 230),
            width=1,
        )
        draw.text(
            (x + pad_x, y + pad_y - box[1]),
            status,
            fill="white",
            font=status_font,
        )
    return canvas


def seed_frames(
    root: Path,
    seed: int,
    width: int,
    height: int,
    max_frames: int | None = None,
):
    paths = [root / f"seed_{seed}" / f"{method}.mp4" for method in METHODS]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing recordings:\n" + "\n".join(missing))

    statuses = [read_status(path) for path in paths]
    readers = [imageio.get_reader(path) for path in paths]
    iterators = [iter(reader) for reader in readers]
    last: list[np.ndarray | None] = [None] * len(readers)
    previous: list[np.ndarray | None] = [None] * len(readers)
    ended = [False] * len(readers)
    panel_width, panel_height = width // 2, height // 2
    emitted_frames = 0
    try:
        while (
            emitted_frames < max_frames
            if max_frames is not None
            else not all(ended)
        ):
            if max_frames is not None and emitted_frames >= max_frames:
                break
            for index, iterator in enumerate(iterators):
                if ended[index]:
                    continue
                try:
                    frame = next(iterator)
                    previous[index] = last[index]
                    last[index] = frame
                except StopIteration:
                    ended[index] = True
                    # MetaDrive may remove the ego vehicle from the final
                    # post-termination render. Freeze the preceding frame so
                    # the collision/out-of-road vehicle remains visible.
                    if previous[index] is not None:
                        last[index] = previous[index]
            if any(frame is None for frame in last):
                continue
            canvas = Image.new("RGB", (width, height), "white")
            positions = (
                (0, 0),
                (panel_width, 0),
                (0, panel_height),
                (panel_width, panel_height),
            )
            for index, (x, y) in enumerate(positions):
                force_final_outcome = (
                    max_frames is not None
                    and emitted_frames == max_frames - 1
                )
                canvas.paste(
                    panel(
                        last[index],
                        METHODS[index],
                        panel_width,
                        panel_height,
                        ended[index] or force_final_outcome,
                        statuses[index],
                    ),
                    (x, y),
                )
            yield np.asarray(canvas)
            emitted_frames += 1
    finally:
        for reader in readers:
            reader.close()


def individual_method_frames(
    root: Path,
    seed: int,
    method: str,
    width: int,
    height: int,
    fps: int,
    seconds: float,
    zoom: float,
):
    """Time-compress one complete recording into a fixed individual segment."""
    video_path = root / f"seed_{seed}" / f"{method}.mp4"
    if not video_path.is_file():
        raise FileNotFoundError(f"Missing recording: {video_path}")
    status = read_status(video_path)
    target_frames = max(1, round(seconds * fps))
    reader = imageio.get_reader(video_path)
    try:
        try:
            source_frames = int(reader.count_frames())
        except Exception:
            source_frames = int(reader.get_length())
        if source_frames <= 0:
            raise ValueError(f"No frames in recording: {video_path}")

        # Avoid the post-termination frame because MetaDrive may remove the
        # ego vehicle there. Even sampling covers the complete episode.
        final_source_index = max(0, source_frames - 2)
        indices = np.linspace(
            0,
            final_source_index,
            target_frames,
            dtype=int,
        )
        representative = trim_black_edges(
            reader.get_data(int(indices[len(indices) // 2]))
        )
        crop_box = road_focused_crop_box(
            representative,
            width,
            height,
            zoom,
        )
        outcome_frames = max(1, round(0.5 * fps))
        for output_index, source_index in enumerate(indices):
            frame = trim_black_edges(reader.get_data(int(source_index)))
            left, top, right, bottom = crop_box
            frame = frame[top:bottom, left:right]
            show_outcome = output_index >= target_frames - outcome_frames
            yield np.asarray(
                panel(
                    frame,
                    DISPLAY_LABELS.get(method, method),
                    width,
                    height,
                    show_outcome,
                    status,
                )
            )
    finally:
        reader.close()


def trim_black_edges(frame: np.ndarray) -> np.ndarray:
    """Remove only near-solid black edge bars; preserve road and vehicle pixels."""
    rgb = frame[:, :, :3]
    near_black = rgb.max(axis=2) < 24
    row_is_bar = near_black.mean(axis=1) > 0.92
    col_is_bar = near_black.mean(axis=0) > 0.92

    top = 0
    while top < len(row_is_bar) and row_is_bar[top]:
        top += 1
    bottom = len(row_is_bar)
    while bottom > top and row_is_bar[bottom - 1]:
        bottom -= 1
    left = 0
    while left < len(col_is_bar) and col_is_bar[left]:
        left += 1
    right = len(col_is_bar)
    while right > left and col_is_bar[right - 1]:
        right -= 1
    if bottom - top < 20 or right - left < 20:
        return frame
    return frame[top:bottom, left:right]


def external_safetypool_frames(
    video_path: Path,
    width: int,
    height: int,
    fps: int,
    zoom: float,
):
    """Render the supplied four-second SafetyPool-only clip as Car 4."""
    if not video_path.is_file():
        raise FileNotFoundError(video_path)
    reader = imageio.get_reader(video_path)
    try:
        source_frames = int(reader.count_frames())
        target_frames = round(4.0 * fps)
        final_source_index = max(0, source_frames - 2)
        indices = np.linspace(
            0,
            final_source_index,
            target_frames,
            dtype=int,
        )
        representative = trim_black_edges(
            reader.get_data(int(indices[len(indices) // 2]))
        )
        crop_box = road_focused_crop_box(
            representative,
            width,
            height,
            zoom,
        )
        for source_index in indices:
            frame = trim_black_edges(reader.get_data(int(source_index)))
            left, top, right, bottom = crop_box
            frame = frame[top:bottom, left:right]
            yield np.asarray(
                panel(
                    frame,
                    DISPLAY_LABELS["SafetyPool"],
                    width,
                    height,
                    False,
                    None,
                )
            )
    finally:
        reader.close()


def road_focused_crop_box(
    frame: np.ndarray,
    output_width: int,
    output_height: int,
    zoom: float,
) -> tuple[int, int, int, int]:
    """Find a stable crop around road markings and vehicles, excluding telemetry."""
    source_height, source_width = frame.shape[:2]
    search_top = min(80, max(0, source_height // 5))
    rgb = frame[search_top:, :, :3].astype(np.int16)
    minimum = rgb.min(axis=2)
    maximum = rgb.max(axis=2)
    # Capture grey road markings and coloured vehicles while rejecting white.
    mask = (minimum < 232) | ((maximum - minimum) > 22)
    ys, xs = np.where(mask)
    if len(xs) < 20:
        return (0, 0, source_width, source_height)

    left = max(0, int(xs.min()) - 35)
    right = min(source_width, int(xs.max()) + 36)
    top = max(0, int(ys.min()) + search_top - 35)
    bottom = min(source_height, int(ys.max()) + search_top + 36)

    center_x = (left + right) / 2
    center_y = (top + bottom) / 2
    crop_width = max(80.0, (right - left) / max(1.0, zoom))
    crop_height = max(80.0, (bottom - top) / max(1.0, zoom))
    target_aspect = output_width / output_height
    if crop_width / crop_height < target_aspect:
        crop_width = crop_height * target_aspect
    else:
        crop_height = crop_width / target_aspect

    crop_width = min(float(source_width), crop_width)
    crop_height = min(float(source_height), crop_height)
    left = int(round(center_x - crop_width / 2))
    top = int(round(center_y - crop_height / 2))
    left = max(0, min(left, source_width - int(crop_width)))
    top = max(0, min(top, source_height - int(crop_height)))
    return (
        left,
        top,
        min(source_width, left + int(crop_width)),
        min(source_height, top + int(crop_height)),
    )


def compose_tiles(
    tiles: list[np.ndarray | None],
    width: int,
    height: int,
) -> np.ndarray:
    """Compose tile numbers 1,2 / 3,4 into a fixed two-by-two canvas."""
    tile_width, tile_height = width // 2, height // 2
    canvas = Image.new("RGB", (width, height), "white")
    positions = (
        (0, 0),
        (tile_width, 0),
        (0, tile_height),
        (tile_width, tile_height),
    )
    for tile, position in zip(tiles, positions):
        if tile is not None:
            canvas.paste(Image.fromarray(tile).convert("RGB"), position)
    draw = ImageDraw.Draw(canvas)
    draw.line(
        (tile_width, 0, tile_width, height),
        fill=(70, 70, 70),
        width=4,
    )
    draw.line(
        (0, tile_height, width, tile_height),
        fill=(70, 70, 70),
        width=4,
    )
    draw.rectangle(
        (0, 0, width - 1, height - 1),
        outline=(70, 70, 70),
        width=3,
    )
    return np.asarray(canvas)


def main() -> None:
    args = parse_args()
    seed_durations: dict[int, float] = {}
    for value in args.seed_duration:
        try:
            seed_text, seconds_text = value.split("=", 1)
            seed = int(seed_text)
            seconds = float(seconds_text)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid --seed-duration {value!r}; expected SEED=SECONDS."
            ) from exc
        if seconds <= 0:
            raise ValueError("--seed-duration seconds must be positive.")
        seed_durations[seed] = seconds
    args.output.parent.mkdir(parents=True, exist_ok=True)
    title_frames = max(0, round(args.title_seconds * args.fps))
    overall_title_frames = max(
        0,
        round(args.overall_title_seconds * args.fps),
    )
    transition_pause_frames = max(
        0,
        round(args.transition_pause_seconds * args.fps),
    )
    with imageio.get_writer(
        args.output,
        fps=args.fps,
        codec="libx264",
        quality=8,
        macro_block_size=None,
    ) as writer:
        if overall_title_frames:
            card = overall_title_card(args.width, args.height, args.seeds)
            for _ in range(overall_title_frames):
                writer.append_data(card)
        tile_width, tile_height = args.width // 2, args.height // 2
        tile_gap_frames = max(0, round(args.tile_gap_seconds * args.fps))
        seed_gap_frames = max(0, round(args.seed_gap_seconds * args.fps))
        for seed_index, seed in enumerate(args.seeds):
            frozen_tiles: list[np.ndarray | None] = [None, None, None, None]
            for play_index, (tile_index, method) in enumerate(TILE_PLAY_ORDER):
                duration = (
                    4.0
                    if seed == 19 and method == "SafetyPool"
                    else args.tile_seconds
                )
                final_tile = None
                if (
                    seed == 19
                    and method == "SafetyPool"
                    and args.seed19_safetypool_video is not None
                ):
                    tile_frames = external_safetypool_frames(
                        args.seed19_safetypool_video,
                        tile_width,
                        tile_height,
                        args.fps,
                        args.individual_zoom,
                    )
                else:
                    tile_frames = individual_method_frames(
                        args.input_root,
                        seed,
                        method,
                        tile_width,
                        tile_height,
                        args.fps,
                        duration,
                        args.individual_zoom,
                    )
                for tile_frame in tile_frames:
                    active_tiles = list(frozen_tiles)
                    active_tiles[tile_index] = tile_frame
                    writer.append_data(
                        compose_tiles(active_tiles, args.width, args.height)
                    )
                    final_tile = tile_frame
                if final_tile is not None:
                    frozen_tiles[tile_index] = final_tile

                is_last_tile = play_index == len(TILE_PLAY_ORDER) - 1
                gap_frames = seed_gap_frames if is_last_tile else tile_gap_frames
                if is_last_tile and seed_index == len(args.seeds) - 1:
                    gap_frames = 0
                frozen_canvas = compose_tiles(
                    frozen_tiles,
                    args.width,
                    args.height,
                )
                for _ in range(gap_frames):
                    writer.append_data(frozen_canvas)
    print(f"Combined comparison video: {args.output.resolve()}")


if __name__ == "__main__":
    main()
