# Zephyr-Odyssey

## 🏔️ Narrative

On the terra-engineered resort planet **Zephyr‑9**, skiing is more than sport — it’s a fusion of speed, gravity tech, and survival instinct. Snow here is created from atmospheric water particles, and thrill-seekers use mag-rail skis to glide just above the terrain, carving trails down gravity-defying slopes. Among these adventurers is **Shepard**, a skilled backcountry pilot with deep knowledge of the mountain’s forgotten infrastructure.

One morning, the skies fracture. A massive orbital solar mirror (part of the planet’s climate array) breaks apart and crashes into the northern ridgeline. The impact triggers a **hyper-velocity avalanche**, heading straight for several colony domes below. With evacuation failing, only one desperate plan remains: manually divert the avalanche using gravity beacon nodes, planted along a harrowing descent through the Zephyr Rift.

### 🎮 Level 1: Avalanche Run

Shepard answers the call. Dropping into the canyon, his AI companion, **A.R.I.E.L.** *(Autonomous Response & Intelligence for Environmental Logistics)*, keeps pace. He must stay ahead of the avalanche, activating gravity beacons at checkpoints to weave together a gravity mesh that reroutes the storm. The race is a blur of light, wind, and ice, ending with a daring leap to a remote tram station — only to find a second, even more unstable avalanche threatening from above.

### 🌩️ Level 2: Storm Break

But now it’s not just snow. **Solar panel shrapnel rains** from the sky, creating new avalanches and chaos. Shepard must climb towards the Weather Control Tower, racing along ancient tramways, leaping across gaps, re-activating lost power, and dodging debris. At the summit, with A.R.I.E.L.’s help, he channels the beacon data into the tower’s planetary grav-core.

As the storm breaks through, Shepard executes the final override. The grav-pulse fires — a silent, blinding flash that collapses the avalanche into crystal dust.  
Dawn breaks. The colony is safe, and Shepard — finally at peace — descends the mountain just for the joy of it.

> **Note:**  
> Assets required to run *Zephyr-Odyssey* (images, audio, video) are **NOT included** in this repository due to size constraints. To request the assets for local development, contact the maintainer.

---

## 🕹️ Game Overview

**Zephyr-Odyssey** is a fast-paced, cinematic, physics-driven action game. Guide Shepard through two story-rich levels packed with dynamic obstacles, particle effects, and immersive narrative moments, all powered by **Python** and **Pygame**.

### ✨ Core Features

- **Two Cinematic Levels**
  - Avalanche-chased descent with timed checkpoints *(Level 1)*
  - Debris-choked climb to the Weather Tower *(Level 2)*

- **Physics-Based Controls**
  - Jump, double jump, shoot obstacles, and mag-ski mechanics

- **Procedural Terrain & Effects**
  - Snow, lava, fog, particle storms, lighting, and animated backgrounds

- **Narrative Cutscenes & VO**
  - In-game storytelling with voiceovers and AI companion overlays

- **Dynamic Obstacles**
  - Ice shards, falling satellites, bugs, crystal spikes, avalanches, and boulders

- **Customizable Configs**
  - Tune difficulty, spawn rates, effects, and more via `config.py`

- **Modern UI/HUD**
  - Animated menus, checkpoints, tutorials, settings, and real-time indicators

---

## 🛠️ Installation

### Requirements

- Python 3.8+
- `pygame`
- `pillow`
- `opencv-python`

### Setup

```bash
pip install pygame pillow opencv-python
```

Clone the repository:

```bash
git clone https://github.com/MrMystery8/Zephyr-Odyssey.git
cd Zephyr-Odyssey
```

> ⚠️ Place required assets in the proper subfolders. Contact the maintainer to request the asset bundle.

Run the game:

```bash
python Main.py
```

---

## 🎮 Controls

| Key        | Action                        |
|------------|-------------------------------|
| Spacebar   | Jump / Double Jump            |
| F          | Shoot (limited ammo)          |
| Arrow Keys | Navigate Menus / Settings     |
| Enter / Esc| Confirm / Back / Cancel       |

> Tutorial prompts appear dynamically during gameplay.

---

## 📁 Directory Structure

```
Zephyr-Odyssey/
├── Main.py              # Main game loop/entry point
├── config.py            # Centralized config & tuning
├── player.py            # Player mechanics, animation
├── terrain.py           # Procedural terrain/environment
├── game_state.py        # State management
├── obstacle.py          # Obstacle base and variants
├── avalanche.py         # Avalanche threat logic
├── boulder.py           # Rolling boulder for L2
├── video_player.py      # Cutscene playback
├── hud.py / ui.py       # HUD, menus, overlays
├── (other .py files)    # Effects, AI, overlays, etc.
└── README.md            # This file
```

---

## 🙌 Credits

**Zephyr-Odyssey**  
A Final Project by Group 32:
- Ayaan Minhas  
- Muhammad Noorullah Baig  
- Ajneya Lal  
- Amal Djasreel Bin Amril

**Special Thanks**  
To **A.R.I.E.L.**, our in-game and in-spirit AI companion.

**Libraries Used**  
`Python` · `Pygame` · `Pillow` · `OpenCV`

---

## 🤝 Contributing

Pull requests welcome!  
Please fork the repo, create a feature branch, document your changes, and open a PR.

For questions, feature ideas, or asset access — contact the maintainer directly.

**Made with ❤️ by the Zephyr-Odyssey Team**
