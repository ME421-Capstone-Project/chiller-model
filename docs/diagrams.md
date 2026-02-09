# Chiller Model Architecture Diagrams

This directory contains **professional, publication-ready** visual architecture diagrams for the chiller-model package.

> 💡 **Tip**: Click any diagram to view it larger. GitHub renders these automatically!

## System Architecture Diagram

High-level overview showing all layers and their relationships.

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#e1f5ff','primaryTextColor':'#000','primaryBorderColor':'#0288d1','lineColor':'#0288d1','secondaryColor':'#fff4e1','tertiaryColor':'#e8f5e9'}}}%%

graph TB
    subgraph ui[" 🖥️  USER INTERFACE LAYER "]
        UI["<b>User Scripts & Notebooks</b><br/>📓 demo.ipynb<br/>📄 examples/*.py<br/>🔧 QUICK_START.py"]
    end
    
    subgraph sim[" ⚙️  SIMULATION LAYER "]
        ENV["<b>SimulationEnvironment</b><br/>🎯 compute_performance()<br/>💨 with_new_wind()<br/>🔄 with_new_model()"]
        OPT["<b>Optimizer</b><br/>🎲 optimize_greedy()<br/>📊 sensitivity_analysis()<br/>📈 compare_configurations()"]
    end
    
    subgraph comp[" 🧩  COMPONENT LAYER "]
        ARRAY["<b>ChillerArray</b><br/>📍 positions_m: (N×2)<br/>❄️ base_cop: 4.0<br/>📉 alpha: 0.7"]
        WIND["<b>WindVector</b><br/>💨 velocity: (vx, vy)<br/>🌡️ temp_k: 298.15<br/>📐 direction, speed"]
        MODEL["<b>InteractionModel</b><br/>🔌 Pluggable Interface<br/>🔁 Swappable at Runtime"]
    end
    
    subgraph models[" 🧮  MODEL LAYER "]
        BASE["<b>BaseInteractionModel</b><br/>📜 Abstract Base Class<br/>⚡ compute_interaction_matrix()"]
        GAUSS["<b>GaussianPlumeModel</b><br/>σ dispersion_coeff: 1.2<br/>🌊 Plume Dispersion<br/>📐 Vectorized NumPy"]
    end
    
    subgraph core[" 🏗️  CORE LAYER "]
        CONFIG["<b>configs.py</b><br/>✅ Pydantic Validation<br/>🛡️ Type Safety<br/>📏 SI Units Enforced"]
        CONST["<b>constants.py</b><br/>🔢 Physical Constants<br/>📊 Default Values<br/>⚖️ Realistic Bounds"]
        SPEC["<b>Data Structures</b><br/>❄️ ChillerSpec (frozen)<br/>📈 ChillerState (immutable)<br/>📦 Results (NamedTuple)"]
    end
    
    UI ==>|"invokes"| ENV
    UI ==>|"invokes"| OPT
    OPT -.->|"uses"| ENV
    
    ENV ==>|"composes"| ARRAY
    ENV ==>|"composes"| WIND
    ENV ==>|"composes"| MODEL
    
    MODEL -.->|"implements"| BASE
    GAUSS -.->|"extends"| BASE
    ENV ==>|"delegates to"| GAUSS
    
    ARRAY -.->|"validated by"| CONFIG
    WIND -.->|"validated by"| CONFIG
    GAUSS -.->|"uses"| CONST
    ARRAY -.->|"creates"| SPEC
    
    classDef uiStyle fill:#e1f5ff,stroke:#0288d1,stroke-width:3px,color:#000
    classDef simStyle fill:#fff4e1,stroke:#ff6f00,stroke-width:3px,color:#000
    classDef compStyle fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px,color:#000
    classDef modelStyle fill:#f3e5f5,stroke:#6a1b9a,stroke-width:3px,color:#000
    classDef coreStyle fill:#fce4ec,stroke:#c2185b,stroke-width:3px,color:#000
    
    class UI uiStyle
    class ENV,OPT simStyle
    class ARRAY,WIND,MODEL compStyle
    class BASE,GAUSS modelStyle
    class CONFIG,CONST,SPEC coreStyle
```

## Data Flow Diagram

Complete execution flow from user input to optimization results.

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'actorBkg':'#e3f2fd','actorBorder':'#1976d2','actorTextColor':'#000','signalColor':'#1976d2','signalTextColor':'#000','labelBoxBkgColor':'#fff9c4','labelBoxBorderColor':'#f57f17'}}}%%

sequenceDiagram
    autonumber
    participant 👤 User
    participant 🏭 ChillerArray
    participant 💨 WindVector
    participant 🧮 GaussianPlume
    participant ⚙️ SimEnv
    participant 🎯 Optimizer
    
    rect rgb(227, 242, 253)
    Note over 👤 User,🏭 ChillerArray: 📦 SETUP PHASE - Component Creation
    👤 User->>+🏭 ChillerArray: create_grid(5×5, spacing=3m)
    🏭 ChillerArray-->>-👤 User: ✅ array (25 chillers)
    
    👤 User->>+💨 WindVector: WindVector(v=5.0 m/s, T=298K)
    💨 WindVector-->>-👤 User: ✅ wind (normalized)
    
    👤 User->>+🧮 GaussianPlume: GaussianPlumeModel(σ=1.2)
    🧮 GaussianPlume-->>-👤 User: ✅ model (ready)
    end
    
    rect rgb(255, 249, 196)
    Note over 👤 User,⚙️ SimEnv: 🔧 INITIALIZATION - Matrix Precomputation
    👤 User->>+⚙️ SimEnv: SimEnv(array, wind, model)
    ⚙️ SimEnv->>+🧮 GaussianPlume: compute_interaction_matrix()
    
    Note right of 🧮 GaussianPlume: Vectorized O(N²) computation:<br/>1. Pairwise displacements<br/>2. Wind projections<br/>3. Gaussian formula<br/>4. Zero upwind/diagonal
    
    🧮 GaussianPlume-->>-⚙️ SimEnv: A (25×25 matrix)
    ⚙️ SimEnv-->>-👤 User: ✅ env (initialized)
    end
    
    rect rgb(232, 245, 233)
    Note over 👤 User,⚙️ SimEnv: 📊 PERFORMANCE CALCULATION
    👤 User->>+⚙️ SimEnv: compute_performance(mask, 100kW)
    
    Note right of ⚙️ SimEnv: Vectorized calculations:<br/>1. Load: 100kW ÷ 25 = 4kW each<br/>2. Temp: rise = mask @ A<br/>3. COP: base/(1 + α·rise)<br/>4. Work: Σ(load/COP)
    
    ⚙️ SimEnv-->>-👤 User: ✅ Result(27.8kW, COP[], rise[])
    end
    
    rect rgb(243, 229, 245)
    Note over 👤 User,🎯 Optimizer: 🎲 OPTIMIZATION - Greedy Search
    👤 User->>+🎯 Optimizer: optimize_greedy(min=15)
    
    loop Each Iteration (until convergence)
        🎯 Optimizer->>+⚙️ SimEnv: Try removing each chiller
        ⚙️ SimEnv-->>-🎯 Optimizer: Performance for each config
        Note right of 🎯 Optimizer: Keep best removal:<br/>Min work = 24.5kW
    end
    
    🎯 Optimizer-->>-👤 User: ✅ Optimal(mask[], 24.5kW, 11.8% savings)
    end
```

## Module Dependency Graph

```mermaid
graph LR
    subgraph core
        configs[configs.py]
        constants[constants.py]
    end
    
    subgraph components
        wind[wind.py]
        chiller[chiller.py]
        chiller_array[chiller_array.py]
    end
    
    subgraph models
        base_interaction[base_interaction.py]
        gaussian_plume[gaussian_plume.py]
    end
    
    subgraph simulation
        environment[environment.py]
        optimizer[optimizer.py]
    end
    
    wind --> configs
    chiller --> configs
    chiller_array --> constants
    
    gaussian_plume --> base_interaction
    gaussian_plume --> constants
    
    environment --> chiller_array
    environment --> wind
    environment --> base_interaction
    
    optimizer --> environment
    
    style configs fill:#ff9999
    style constants fill:#ff9999
    style wind fill:#99ccff
    style chiller fill:#99ccff
    style chiller_array fill:#99ccff
    style base_interaction fill:#99ff99
    style gaussian_plume fill:#99ff99
    style environment fill:#ffff99
    style optimizer fill:#ffff99
```

## Physics Calculation Flow

```mermaid
flowchart TD
    START([Start: Active Mask + Load]) --> DIST[Distribute Load Evenly<br/>load_per_unit = total_load / n_active]
    DIST --> TEMP[Compute Temperature Rise<br/>temp_rise = active_mask @ A]
    TEMP --> COP[Degrade COP<br/>cop = base_cop / (1 + alpha * temp_rise)]
    COP --> WORK[Calculate Electrical Work<br/>work = sum(load / cop) for active units]
    WORK --> RESULT[Return PerformanceResult<br/>total_work_kw, cop_array, etc.]
    RESULT --> END([End])
    
    style START fill:#e1f5ff
    style DIST fill:#fff4e1
    style TEMP fill:#ffe1e1
    style COP fill:#e1ffe1
    style WORK fill:#f5e1ff
    style RESULT fill:#e1fff5
    style END fill:#e1f5ff
```

## Greedy Optimization Algorithm

```mermaid
flowchart TD
    START([Start: All Chillers Active]) --> BASELINE[Compute Baseline Performance<br/>baseline_work = performance with all active]
    BASELINE --> INIT[Initialize:<br/>best_mask = all active<br/>best_work = baseline_work]
    INIT --> CHECK{n_active ><br/>min_active?}
    CHECK -->|No| DONE[Return OptimizationResult]
    CHECK -->|Yes| LOOP[For each active chiller i]
    LOOP --> TRY[Try: mask_i = mask with chiller i OFF]
    TRY --> EVAL[Compute: work_i = performance(mask_i).work]
    EVAL --> BETTER{work_i <<br/>best_work?}
    BETTER -->|Yes| UPDATE[Update:<br/>best_removal = i<br/>best_work = work_i]
    BETTER -->|No| NEXT{More chillers<br/>to try?}
    UPDATE --> NEXT
    NEXT -->|Yes| LOOP
    NEXT -->|No| IMPROVE{Found<br/>improvement?}
    IMPROVE -->|Yes| APPLY[Apply best removal:<br/>mask[best_removal] = False<br/>iterations += 1]
    IMPROVE -->|No| DONE
    APPLY --> CHECK
    DONE --> END([End: Optimal Configuration])
    
    style START fill:#e1f5ff
    style BASELINE fill:#fff4e1
    style INIT fill:#fff4e1
    style CHECK fill:#ffe1e1
    style LOOP fill:#e1ffe1
    style TRY fill:#f5e1ff
    style EVAL fill:#f5e1ff
    style BETTER fill:#ffe1e1
    style UPDATE fill:#e1fff5
    style NEXT fill:#ffe1e1
    style IMPROVE fill:#ffe1e1
    style APPLY fill:#e1fff5
    style DONE fill:#e1f5ff
    style END fill:#e1f5ff
```

## Class Relationships (Composition Pattern)

```mermaid
classDiagram
    class SimulationEnvironment {
        -ChillerArray chiller_array
        -WindVector wind
        -BaseInteractionModel interaction_model
        -NDArray interaction_matrix
        +compute_performance() PerformanceResult
        +with_new_wind() SimulationEnvironment
        +with_new_model() SimulationEnvironment
    }
    
    class ChillerArray {
        +NDArray positions_m
        +float base_cop
        +float alpha
        +create_grid() ChillerArray
        +create_random() ChillerArray
    }
    
    class WindVector {
        +tuple velocity_m_per_s
        +float ambient_temp_k
        +direction NDArray
        +speed_m_per_s float
        +from_speed_and_angle() WindVector
    }
    
    class BaseInteractionModel {
        <<abstract>>
        +compute_interaction_matrix()* NDArray
        +validate_matrix() None
    }
    
    class GaussianPlumeModel {
        +float dispersion_coeff
        +compute_interaction_matrix() NDArray
        +compute_longitudinal_distances() NDArray
        +compute_lateral_distances() NDArray
    }
    
    class Optimizer {
        -SimulationEnvironment environment
        +float total_load_kw
        +optimize_greedy() OptimizationResult
        +sensitivity_analysis() NDArray
    }
    
    class PerformanceResult {
        <<immutable>>
        +float total_work_kw
        +NDArray cop_array
        +NDArray temp_rise_array
        +float load_per_unit_kw
    }
    
    class OptimizationResult {
        <<immutable>>
        +NDArray optimal_mask
        +float optimal_work_kw
        +float baseline_work_kw
        +float savings_fraction
        +PerformanceResult performance
    }
    
    SimulationEnvironment *-- ChillerArray : composes
    SimulationEnvironment *-- WindVector : composes
    SimulationEnvironment *-- BaseInteractionModel : composes
    SimulationEnvironment ..> PerformanceResult : creates
    GaussianPlumeModel --|> BaseInteractionModel : implements
    Optimizer *-- SimulationEnvironment : uses
    Optimizer ..> OptimizationResult : creates
    OptimizationResult *-- PerformanceResult : contains
```

## Usage Instructions

### For Sphinx Documentation

Add to your `conf.py`:

```python
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinxcontrib.mermaid',  # pip install sphinxcontrib-mermaid
]
```

Include in your `.rst` files:

```rst
.. mermaid:: diagrams.md
   :caption: System Architecture
```

### For GitHub/Markdown Viewers

GitHub natively renders Mermaid diagrams in markdown files. Just include the fenced code blocks with `mermaid` language tag.

### For Interactive Viewing

Use [Mermaid Live Editor](https://mermaid.live/) to:
1. Copy any diagram code above
2. Paste into the editor
3. View, edit, and export as SVG/PNG

### For LaTeX/Academic Papers

Export diagrams as SVG from Mermaid Live Editor, then convert to PDF:

```bash
inkscape diagram.svg --export-pdf=diagram.pdf
```

Include in LaTeX:
```latex
\includegraphics[width=\textwidth]{diagram.pdf}
```

## Diagram Maintenance

When adding new modules or changing architecture:

1. Update the relevant diagram(s) in this file
2. Regenerate documentation: `cd docs && make html`
3. Verify diagrams render correctly
4. Commit both source and generated docs

## Design Principles Illustrated

These diagrams emphasize:

- **Composition over Inheritance**: Classes hold instances, not inherit
- **Immutability**: Results are NamedTuples/frozen dataclasses
- **Separation of Concerns**: Clear layer boundaries
- **Dependency Inversion**: High-level modules depend on abstractions
- **Single Responsibility**: Each module has one clear purpose
