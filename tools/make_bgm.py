# -*- coding: utf-8 -*-
"""リール用のBGMを作る（すべてこのプログラムで合成したオリジナル音源。著作権の確認が不要）。
  python tools/make_bgm.py   → assets/bgm/*.m4a
必要：numpy、ffmpeg（作る時だけ。投稿の自動処理ではできあがったファイルを使う）"""
import os, subprocess, wave
import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "bgm")
NOTE = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}


def hz(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave + 1) - 69) / 12)


def env(n, attack=0.01, decay=1.2):
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    return a * np.exp(-t / decay)


def keys(freq, dur, vol=0.12, decay=1.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    # エレピ風：基音＋倍音、わずかなビブラート
    vib = 1 + 0.002 * np.sin(2 * np.pi * 5 * t)
    x = (np.sin(2 * np.pi * freq * vib * t) + 0.35 * np.sin(4 * np.pi * freq * t) * np.exp(-t * 3)
         + 0.08 * np.sin(6 * np.pi * freq * t) * np.exp(-t * 6))
    return vol * x * env(n, 0.008, decay)


def bass(freq, dur, vol=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.15 * np.sin(4 * np.pi * freq * t)
    return vol * x * env(n, 0.01, 0.5)


def kick(vol=0.5):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    f = 50 + 70 * np.exp(-t * 30)
    return vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 12)


def noise_hit(dur, vol, decay, rng, lp=0.3):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    y = np.zeros(n)                      # 簡単なローパスでやわらかく
    for i in range(1, n):
        y[i] = y[i - 1] + lp * (x[i] - y[i - 1])
    t = np.arange(n) / SR
    return vol * y * np.exp(-t / decay)


def add(buf, x, at):
    i = int(at * SR)
    j = min(len(buf), i + len(x))
    if i < len(buf):
        buf[i:j] += x[: j - i]


def lowpass(x, a):
    y = np.zeros_like(x)
    for i in range(1, len(x)):
        y[i] = y[i - 1] + a * (x[i] - y[i - 1])
    return y


def song(name, bpm, prog, bars=12, seed=0, swing=0.06, hats=True):
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    total = bars * 4 * beat
    buf = np.zeros(int((total + 2) * SR))
    snare = noise_hit(0.25, 0.10, 0.06, rng, lp=0.5)
    hat = noise_hit(0.05, 0.035, 0.015, rng, lp=0.9)
    for b in range(bars):
        root, chord = prog[b % len(prog)]
        t0 = b * 4 * beat
        # 和音：1拍目と2拍目の裏
        for at, v in ((0, 1.0), (1.5 + swing, 0.7)):
            for (n, o) in chord:
                add(buf, keys(hz(n, o), beat * 2.5, 0.10 * v), t0 + at * beat)
        # ベース：1拍目と3拍目
        add(buf, bass(hz(root, 2), beat * 1.8), t0)
        add(buf, bass(hz(root, 2), beat * 1.2, 0.16), t0 + 2.5 * beat)
        # リズム（最初の1小節は和音だけで入る）
        if b >= 1:
            add(buf, kick(), t0)
            add(buf, kick(0.35), t0 + 2.5 * beat)
            add(buf, snare, t0 + beat)
            add(buf, snare, t0 + 3 * beat)
            if hats:
                for k in range(8):
                    add(buf, hat * (1.0 if k % 2 == 0 else 0.6), t0 + (k * 0.5 + (swing if k % 2 else 0)) * beat)
    buf = lowpass(buf, 0.35)              # 角を取って落ち着いた音に
    buf = buf[: int(total * SR)]
    fade = int(1.5 * SR)
    buf[-fade:] *= np.linspace(1, 0, fade)
    buf[: int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
    buf = buf / np.max(np.abs(buf)) * 0.89
    os.makedirs(OUT, exist_ok=True)
    wav = os.path.join(OUT, name + ".wav")
    with wave.open(wav, "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((buf * 32767).astype("<i2").tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "2", "-c:a", "aac", "-b:a", "160k",
                    os.path.join(OUT, name + ".m4a")], check=True)
    os.remove(wav)
    print(name, f"{total:.1f}秒")


if __name__ == "__main__":
    # 1. やわらかいローファイ（F△7 → E m7 → D m7 → C△7）
    song("01_soft_lofi", 88, [("F", [("A", 4), ("C", 5), ("E", 5)]), ("E", [("G", 4), ("B", 4), ("D", 5)]),
                               ("D", [("F", 4), ("A", 4), ("C", 5)]), ("C", [("E", 4), ("G", 4), ("B", 4)])], seed=1)
    # 2. 明るい朝（C → G → A m → F）
    song("02_morning", 100, [("C", [("E", 4), ("G", 4), ("C", 5)]), ("G", [("D", 4), ("G", 4), ("B", 4)]),
                              ("A", [("E", 4), ("A", 4), ("C", 5)]), ("F", [("F", 4), ("A", 4), ("C", 5)])], seed=2)
    # 3. 落ち着いた夜（D m9 → G7 → C△7 → A m7）
    song("03_calm", 80, [("D", [("F", 4), ("A", 4), ("E", 5)]), ("G", [("F", 4), ("B", 4), ("D", 5)]),
                          ("C", [("E", 4), ("G", 4), ("B", 4)]), ("A", [("G", 4), ("C", 5), ("E", 5)])], seed=3, hats=False)
