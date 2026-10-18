#!/usr/bin/env python3
"""Assemble genuine reviewed chapter cuts. Never synthesize missing footage.

This helper is offline, uses Python's standard library and existing ffmpeg tools,
requires explicit reviewed inputs, and writes the final master only after a real
successful encode. It does not validate the truth of an acceptance attestation.
"""
import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

VIDEO = Path(__file__).resolve().parent
EXPECTED = [
    '00-cover', '01-context', '02-bronze', '03-silver', '04-gold', '05-ml',
    '06-ailh', '07-notebook-oac', '08-agent-builder', '09-testing-deployment',
    '10-agent-hub', '11-streamlit', '12-close',
]
FINAL = VIDEO / 'final' / 'aidp-financial-investigation-copilot.mp4'
SIDECAR = FINAL.with_suffix('.en.srt')


def path_value(value, label, errors):
    if not isinstance(value, str) or not value.strip():
        errors.append(f'{label}: missing path (null inputs cannot be rendered)')
        return None
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = VIDEO / p
    p = p.resolve()
    if not p.is_file() or p.stat().st_size == 0:
        errors.append(f'{label}: file does not exist or is empty')
        return None
    return p


def probe(path):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise ValueError('ffprobe could not read a media input')
    return json.loads(result.stdout)


def duration(info):
    value = float(info.get('format', {}).get('duration', 0))
    if not math.isfinite(value) or value <= 0:
        raise ValueError('media duration is absent or invalid')
    return value


def srt_time(value):
    match = re.fullmatch(r'(\d{2,}):(\d{2}):(\d{2}),(\d{3})', value)
    if not match:
        raise ValueError('caption time must use HH:MM:SS,mmm')
    h, m, s, ms = map(int, match.groups())
    if m > 59 or s > 59:
        raise ValueError('caption minute/second is invalid')
    return h * 3600 + m * 60 + s + ms / 1000


def check_captions(path, total, errors):
    try:
        content = path.read_text(encoding='utf-8-sig').strip()
        blocks = re.split(r'\r?\n\s*\r?\n', content)
        last_end = 0.0
        if not content:
            raise ValueError('caption file is empty')
        for index, block in enumerate(blocks, 1):
            lines = block.splitlines()
            if len(lines) < 3 or lines[0].strip() != str(index):
                raise ValueError(f'cue {index}: expected sequential SRT index')
            times = lines[1].split(' --> ')
            if len(times) != 2:
                raise ValueError(f'cue {index}: invalid time range')
            start, end = map(srt_time, times)
            if start < last_end - 0.001 or end <= start or end > total + 0.05:
                raise ValueError(f'cue {index}: overlap, reversed range or end beyond footage')
            body = lines[2:]
            if len(body) > 2 or any(len(re.sub(r'<[^>]+>', '', x)) > 55 for x in body):
                raise ValueError(f'cue {index}: exceeds two lines or 55 characters per line')
            if any(re.search(r'<[^>]+>|\{.*?\}', x) for x in body):
                raise ValueError(f'cue {index}: remove caption styling/position overrides')
            if len(' '.join(body)) / (end - start) > 24:
                raise ValueError(f'cue {index}: more than 24 characters per second')
            last_end = end
    except (ValueError, OSError) as exc:
        errors.append(f'captions: {exc}')


def collect(manifest):
    errors = []
    clips = manifest.get('clips')
    if not isinstance(clips, list) or [c.get('chapter_id') for c in clips] != EXPECTED:
        errors.append('clips: all 13 chapter IDs are required in the prescribed order')
        clips = clips if isinstance(clips, list) else []
    prepared = []
    for clip in clips:
        label = str(clip.get('chapter_id', 'unknown chapter'))
        p = path_value(clip.get('path'), label + ' reviewed cut', errors)
        source = path_value(clip.get('source_path'), label + ' original source', errors)
        if clip.get('reviewed_for_publication') is not True:
            errors.append(label + ': reviewed_for_publication must be true after inspection')
        # Silence, synthetic still loops and null trims are never guessed.
        first, last = clip.get('in_seconds'), clip.get('out_seconds')
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in (first, last)):
            errors.append(label + ': explicit finite in_seconds/out_seconds are required')
        elif first < 0 or last <= first:
            errors.append(label + ': invalid selected media range')
        elif p and source:
            prepared.append((label, p, float(first), float(last)))
    voice_info = manifest.get('voice') or {}
    voice = path_value(voice_info.get('path'), 'voice', errors)
    if voice_info.get('reviewed') is not True:
        errors.append('voice: reviewed must be true for the selected final track')
    caption_info = manifest.get('captions') or {}
    captions = path_value(caption_info.get('path'), 'captions', errors)
    if caption_info.get('reviewed') is not True:
        errors.append('captions: reviewed must be true after correction against the final voice')
    if caption_info.get('language') != 'en':
        errors.append('captions: this English production requires language=en')
    if captions and captions.suffix.lower() != '.srt':
        errors.append('captions: a UTF-8 .srt is required')
    path_value(manifest.get('brand_wordmark_path'), 'supplied brand wordmark', errors)
    acceptance = manifest.get('acceptance') or {}
    path_value(acceptance.get('record_path'), 'acceptance record', errors)
    if not acceptance.get('reviewer'):
        errors.append('acceptance: reviewer is required')
    mode = acceptance.get('cut_mode')
    if mode == 'reconciled_hybrid':
        for field in ('context_continuity_passed', 'content_reconciliation_passed'):
            if acceptance.get(field) is not True:
                errors.append(f'acceptance: {field} must pass for a hybrid-success cut')
        for field in ('tested_at_utc', 'period', 'account', 'snapshot'):
            if not acceptance.get(field):
                errors.append(f'acceptance: {field} is required for a hybrid-success cut')
        for field in ('sql_results_path', 'retrieved_policy_path'):
            path_value(acceptance.get(field), 'acceptance ' + field, errors)
    elif mode == 'limitation_led':
        if acceptance.get('limitation_visible_and_spoken') is not True:
            errors.append('acceptance: limitation-led cut must retain the visible and spoken caveat')
    else:
        errors.append('acceptance: select reconciled_hybrid or limitation_led after review')
    review = manifest.get('export_review') or {}
    if review.get('no_sensitive_values_visible') is not True:
        errors.append('review: inspect all source cuts and confirm no_sensitive_values_visible=true')
    if FINAL.exists() or SIDECAR.exists():
        errors.append('final: existing master or sidecar will not be overwritten; preserve it before a new render')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        errors.append('tools: existing ffmpeg and ffprobe are required; nothing will be installed')
    if errors:
        return errors, None
    try:
        total = 0.0
        for label, p, first, last in prepared:
            info = probe(p)
            if not any(s.get('codec_type') == 'video' for s in info.get('streams', [])):
                raise ValueError(label + ': reviewed cut contains no video')
            if last > duration(info) + 0.04:
                raise ValueError(label + ': selected end exceeds actual media duration')
            # FFmpeg output is 30fps; demand frame-aligned edits to prevent drift.
            if any(abs(x * 30 - round(x * 30)) > 0.002 for x in (first, last)):
                raise ValueError(label + ': trims must align to a 30fps output frame')
            total += last - first
        vinfo = probe(voice)
        if not any(s.get('codec_type') == 'audio' for s in vinfo.get('streams', [])):
            raise ValueError('voice input contains no audio')
        voice_seconds = duration(vinfo)
        if voice_seconds > total + 0.04 or voice_seconds < total - 1.0:
            raise ValueError('voice must span the full selected cut, allowing at most one second of natural tail silence; re-edit rather than stretch or loop')
        check_captions(captions, total, errors)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
    return errors, (prepared, voice, captions, total)


def render(data):
    clips, voice, captions, total = data
    work_parent = VIDEO / 'source'
    work_parent.mkdir(exist_ok=True)
    FINAL.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.assembly-', dir=work_parent) as temp:
        work = Path(temp)
        shutil.copyfile(captions, work / 'captions.srt')
        args = ['ffmpeg', '-hide_banner', '-nostdin', '-n']
        for _, path, first, last in clips:
            args += ['-ss', f'{first:.6f}', '-t', f'{last-first:.6f}', '-i', str(path)]
        args += ['-i', str(voice)]
        graph = []
        for i in range(len(clips)):
            # A 160px caption band is below, not over, the scaled UI footage.
            graph.append(
                f'[{i}:v:0]setpts=PTS-STARTPTS,fps=30,'
                'scale=1920:920:force_original_aspect_ratio=decrease:flags=lanczos,'
                f'pad=1920:1080:(ow-iw)/2:0:color=0xF5F1E9,setsar=1[v{i}]'
            )
        graph.append(''.join(f'[v{i}]' for i in range(len(clips))) + f'concat=n={len(clips)}:v=1:a=0[cut]')
        style = (
            'FontName=Arial,Fontsize=34,PrimaryColour=&H00FFFFFF,'
            'OutlineColour=&H80000000,BackColour=&H80000000,BorderStyle=3,'
            'Outline=10,Shadow=0,Alignment=2,MarginV=38,MarginL=120,MarginR=120'
        )
        graph.append(f"[cut]subtitles=filename=captions.srt:force_style='{style}'[out]")
        candidate = work / 'master.mp4'
        args += [
            '-filter_complex', ';'.join(graph), '-map', '[out]', '-map', f'{len(clips)}:a:0',
            '-af', 'apad=pad_dur=1', '-t', f'{total:.6f}',
            '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart',
            '-map_metadata', '-1', str(candidate),
        ]
        subprocess.run(args, cwd=work, check=True)
        encoded = probe(candidate)
        if abs(duration(encoded) - total) > 0.15:
            raise ValueError('encoded duration does not match the selected real footage')
        # No final-named placeholder or failed encode is ever written.
        if FINAL.exists() or SIDECAR.exists():
            raise ValueError('a final file appeared during rendering; refusing to overwrite')
        candidate.replace(FINAL)
        shutil.copyfile(captions, SIDECAR)
    print('Encoded master and English SRT exist. Watch the complete video, check the caption band, and measure final chapters before publication.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--check', action='store_true', help='preflight only; create no media')
    action.add_argument('--render', action='store_true', help='encode only after the complete preflight passes')
    opts = parser.parse_args()
    try:
        manifest = json.loads(opts.manifest.read_text(encoding='utf-8'))
        if not isinstance(manifest, dict):
            raise ValueError('manifest must be a JSON object')
        errors, data = collect(manifest)
        if errors:
            print('Preflight blocked; no media output was created:', file=sys.stderr)
            for error in errors:
                print('- ' + error, file=sys.stderr)
            return 2
        print(f'Preflight passed for {len(data[0])} genuine chapter cuts; selected duration {data[3]:.2f}s. Review attestations are supplied by the producer, not certified by this helper.')
        if opts.render:
            render(data)
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f'Assembly stopped: {exc}. No successful delivery is claimed.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
