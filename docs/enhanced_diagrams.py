"""
Enhanced Architecture Diagrams for Chiller Model
=================================================

This module contains production-quality diagrams using various formats.
Choose the format that best suits your documentation needs.
"""

# ==============================================================================
# OPTION 1: Enhanced Mermaid with Styling
# ==============================================================================

SYSTEM_ARCHITECTURE_STYLED = """
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
"""

DATA_FLOW_ENHANCED = """
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
"""

PHYSICS_PIPELINE_STYLED = """
```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#e8f5e9','primaryTextColor':'#000','primaryBorderColor':'#2e7d32','lineColor':'#1976d2','secondaryColor':'#fff3e0','tertiaryColor':'#e1f5ff'}}}%%

flowchart TB
    START([🚀 START<br/>Active Mask + Total Load])
    
    style START fill:#e3f2fd,stroke:#1565c0,stroke-width:4px
    
    START --> VALIDATE{✅ Validation<br/>n_active > 0?}
    
    VALIDATE -->|❌ No| ERROR([⚠️ ERROR<br/>Return work = ∞])
    VALIDATE -->|✅ Yes| DIST
    
    DIST[📊 Distribute Load<br/>━━━━━━━━━━━━━<br/>load_per_unit = total_load ÷ n_active<br/><br/>Example: 100kW ÷ 25 = 4.0 kW/unit]
    
    DIST --> TEMP
    
    TEMP[🌡️ Temperature Rise<br/>━━━━━━━━━━━━━<br/>temp_rise = active_mask @ A<br/><br/>Matrix multiply O(N²)<br/>Captures upwind thermal impact]
    
    TEMP --> COP
    
    COP[❄️ COP Degradation<br/>━━━━━━━━━━━━━<br/>cop = base_cop ÷ (1 + α × temp_rise)<br/><br/>Physics: Higher temp → Lower efficiency<br/>Typical α = 0.7]
    
    COP --> WORK
    
    WORK[⚡ Electrical Work<br/>━━━━━━━━━━━━━<br/>work_i = load_i ÷ cop_i<br/>total_work = Σ work_i for active units<br/><br/>Vectorized sum over active chillers]
    
    WORK --> RESULT
    
    RESULT[📦 Package Results<br/>━━━━━━━━━━━━━<br/>PerformanceResult:<br/>• total_work_kw<br/>• cop_array[N]<br/>• temp_rise_array[N]<br/>• load_per_unit_kw]
    
    RESULT --> END([🎯 END<br/>Return Immutable Result])
    
    style VALIDATE fill:#fff3e0,stroke:#e65100,stroke-width:3px
    style ERROR fill:#ffebee,stroke:#c62828,stroke-width:3px
    style DIST fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    style TEMP fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    style COP fill:#e1f5ff,stroke:#0277bd,stroke-width:3px
    style WORK fill:#f3e5f5,stroke:#6a1b9a,stroke-width:3px
    style RESULT fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    style END fill:#e8f5e9,stroke:#2e7d32,stroke-width:4px
```
"""

OPTIMIZATION_ALGORITHM_STYLED = """
```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#f3e5f5','primaryTextColor':'#000','primaryBorderColor':'#6a1b9a'}}}%%

flowchart TD
    START([🎯 START<br/><b>Greedy Optimization</b><br/>All Chillers Active])
    
    START --> BASELINE[📊 Compute Baseline<br/>━━━━━━━━━━━━━<br/>Performance with ALL active<br/>baseline_work = 27.8 kW<br/><i>Establishes reference point</i>]
    
    BASELINE --> INIT[🔧 Initialize<br/>━━━━━━━━━━━━━<br/>best_mask = all TRUE<br/>best_work = baseline<br/>iteration = 0]
    
    INIT --> CHECK_MIN
    
    CHECK_MIN{🔍 Check Constraint<br/>━━━━━━━━━━━━━<br/>n_active > min_active?}
    
    CHECK_MIN -->|❌ No<br/>Constraint violated| DONE
    CHECK_MIN -->|✅ Yes<br/>Can remove more| LOOP
    
    LOOP[🔄 For Each Active Chiller i<br/>━━━━━━━━━━━━━<br/>Test removal impact]
    
    LOOP --> TRY[🧪 Trial Removal<br/>━━━━━━━━━━━━━<br/>mask_trial = mask.copy()<br/>mask_trial[i] = FALSE<br/><i>Temporarily disable chiller i</i>]
    
    TRY --> EVAL[⚙️ Evaluate Performance<br/>━━━━━━━━━━━━━<br/>result = compute_performance(mask_trial)<br/>work_i = result.total_work_kw<br/><i>Full physics simulation</i>]
    
    EVAL --> COMPARE{📉 Better Than Best?<br/>━━━━━━━━━━━━━<br/>work_i < best_work?}
    
    COMPARE -->|✅ Yes<br/>Found improvement| UPDATE[💾 Update Best<br/>━━━━━━━━━━━━━<br/>best_removal = i<br/>best_work = work_i<br/><i>Track this candidate</i>]
    
    COMPARE -->|❌ No<br/>Not better| NEXT
    UPDATE --> NEXT
    
    NEXT{🔄 More Chillers?<br/>━━━━━━━━━━━━━<br/>Loop complete?}
    
    NEXT -->|No<br/>Keep testing| LOOP
    NEXT -->|Yes<br/>All tested| IMPROVE
    
    IMPROVE{✨ Found Improvement?<br/>━━━━━━━━━━━━━<br/>best_removal != -1?}
    
    IMPROVE -->|❌ No<br/>Converged| DONE
    IMPROVE -->|✅ Yes<br/>Apply removal| APPLY
    
    APPLY[✂️ Apply Removal<br/>━━━━━━━━━━━━━<br/>mask[best_removal] = FALSE<br/>iteration += 1<br/><i>Permanently disable chiller</i>]
    
    APPLY --> CHECK_MIN
    
    DONE[📦 Package Results<br/>━━━━━━━━━━━━━<br/>OptimizationResult:<br/>• optimal_mask<br/>• optimal_work = 24.5 kW<br/>• baseline_work = 27.8 kW<br/>• savings = 11.8%<br/>• iterations = 10]
    
    DONE --> END([🏁 END<br/><b>Optimal Configuration Found</b>])
    
    style START fill:#e3f2fd,stroke:#1565c0,stroke-width:4px
    style BASELINE fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    style INIT fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    style CHECK_MIN fill:#fff3e0,stroke:#e65100,stroke-width:3px
    style LOOP fill:#e1f5ff,stroke:#0277bd,stroke-width:3px
    style TRY fill:#f3e5f5,stroke:#6a1b9a,stroke-width:3px
    style EVAL fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    style COMPARE fill:#fff3e0,stroke:#e65100,stroke-width:3px
    style UPDATE fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    style NEXT fill:#fff3e0,stroke:#e65100,stroke-width:3px
    style IMPROVE fill:#fff3e0,stroke:#e65100,stroke-width:3px
    style APPLY fill:#a5d6a7,stroke:#2e7d32,stroke-width:4px
    style DONE fill:#c5e1a5,stroke:#558b2f,stroke-width:3px
    style END fill:#81c784,stroke:#2e7d32,stroke-width:4px
```
"""

CLASS_DIAGRAM_STYLED = """
```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#e3f2fd','primaryTextColor':'#000','primaryBorderColor':'#1976d2','fontSize':'14px'}}}%%

classDiagram
    direction TB
    
    class SimulationEnvironment {
        <<orchestrator>>
        -ChillerArray chiller_array
        -WindVector wind
        -BaseInteractionModel model
        -NDArray[float64] _interaction_matrix
        ━━━━━━━━━━━━━━━━━━━━━
        +compute_performance(mask, load) PerformanceResult
        +compute_cop_at_position(idx, mask) float
        +get_thermal_impact_on(idx) NDArray
        +with_new_wind(wind) SimulationEnvironment
        +with_new_model(model) SimulationEnvironment
        ━━━━━━━━━━━━━━━━━━━━━
        📊 Composition Pattern
        ⚡ Vectorized Operations
    }
    
    class ChillerArray {
        <<component>>
        +NDArray[float64] positions_m
        +float base_cop
        +float alpha
        ━━━━━━━━━━━━━━━━━━━━━
        +num_chillers int
        +x_positions_m NDArray
        +y_positions_m NDArray
        +centroid_m NDArray
        +get_bounding_box() tuple
        ━━━━━━━━━━━━━━━━━━━━━
        +create_grid(rows, cols)$ ChillerArray
        +create_random(n, area)$ ChillerArray
        ━━━━━━━━━━━━━━━━━━━━━
        📍 Spatial Layout
        ❄️ Homogeneous Units
    }
    
    class WindVector {
        <<component>>
        +tuple[float, float] velocity_m_per_s
        +float ambient_temp_k
        ━━━━━━━━━━━━━━━━━━━━━
        +direction NDArray «computed»
        +speed_m_per_s float «computed»
        +velocity_array NDArray «computed»
        ━━━━━━━━━━━━━━━━━━━━━
        +from_config(config)$ WindVector
        +from_speed_and_angle(v, θ, T)$ WindVector
        ━━━━━━━━━━━━━━━━━━━━━
        💨 Atmospheric Conditions
        🔒 Frozen (Immutable)
    }
    
    class BaseInteractionModel {
        <<abstract>>
        ━━━━━━━━━━━━━━━━━━━━━
        +compute_interaction_matrix(pos, wind)* NDArray
        +validate_matrix(A, n) None
        ━━━━━━━━━━━━━━━━━━━━━
        🔌 Pluggable Interface
        ⚡ Must Use Vectorization
    }
    
    class GaussianPlumeModel {
        <<concrete>>
        +float dispersion_coeff
        ━━━━━━━━━━━━━━━━━━━━━
        +compute_interaction_matrix(pos, wind) NDArray
        +compute_longitudinal_distances(pos, wind) NDArray
        +compute_lateral_distances(pos, wind) NDArray
        ━━━━━━━━━━━━━━━━━━━━━
        🌊 Gaussian Dispersion
        📐 O(N²) Vectorized
    }
    
    class Optimizer {
        <<strategy>>
        -SimulationEnvironment environment
        +float total_load_kw
        ━━━━━━━━━━━━━━━━━━━━━
        +optimize_greedy(min_active, max_iter) OptimizationResult
        +evaluate_configuration(mask) PerformanceResult
        +compare_configurations(masks) list
        +sensitivity_analysis(mask) NDArray
        ━━━━━━━━━━━━━━━━━━━━━
        🎲 Greedy Algorithm
        📊 O(N³) Complexity
    }
    
    class PerformanceResult {
        <<immutable>>
        +float total_work_kw
        +NDArray[float64] cop_array
        +NDArray[float64] temp_rise_array
        +float load_per_unit_kw
        ━━━━━━━━━━━━━━━━━━━━━
        +mean_cop float «property»
        +effective_cop float «property»
        ━━━━━━━━━━━━━━━━━━━━━
        📦 NamedTuple
        🔒 Immutable Result
    }
    
    class OptimizationResult {
        <<immutable>>
        +NDArray[bool] optimal_mask
        +float optimal_work_kw
        +float baseline_work_kw
        +float savings_fraction
        +PerformanceResult performance
        +int iterations
        ━━━━━━━━━━━━━━━━━━━━━
        +num_active int «property»
        +savings_kw float «property»
        ━━━━━━━━━━━━━━━━━━━━━
        📦 NamedTuple
        ✨ Complete Solution
    }
    
    %% Composition relationships
    SimulationEnvironment *-- "1" ChillerArray : composes
    SimulationEnvironment *-- "1" WindVector : composes
    SimulationEnvironment *-- "1" BaseInteractionModel : composes
    
    %% Inheritance
    GaussianPlumeModel --|> BaseInteractionModel : implements
    
    %% Usage relationships
    Optimizer o-- "1" SimulationEnvironment : uses
    SimulationEnvironment ..> PerformanceResult : creates
    Optimizer ..> OptimizationResult : creates
    OptimizationResult *-- "1" PerformanceResult : contains
    
    %% Styling
    style SimulationEnvironment fill:#fff4e1,stroke:#ff6f00,stroke-width:3px
    style ChillerArray fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    style WindVector fill:#e8f5e9,stroke:#2e7d32,stroke-width:3px
    style BaseInteractionModel fill:#f3e5f5,stroke:#6a1b9a,stroke-width:3px
    style GaussianPlumeModel fill:#f3e5f5,stroke:#6a1b9a,stroke-width:3px
    style Optimizer fill:#fff4e1,stroke:#ff6f00,stroke-width:3px
    style PerformanceResult fill:#e1f5ff,stroke:#0277bd,stroke-width:3px
    style OptimizationResult fill:#e1f5ff,stroke:#0277bd,stroke-width:3px
```
"""

# ==============================================================================
# OPTION 2: D2 Diagram Language (Modern, Very Pretty)
# ==============================================================================

SYSTEM_ARCHITECTURE_D2 = """
# Install D2: https://d2lang.com/
# Render: d2 architecture.d2 architecture.svg

direction: down

title: {
  label: Chiller Model System Architecture
  near: top-center
  style: {
    font-size: 24
    bold: true
  }
}

user_layer: {
  label: "🖥️  USER INTERFACE LAYER"
  style.fill: "#e1f5ff"
  style.stroke: "#0288d1"
  style.stroke-width: 3
  
  scripts: {
    label: "User Scripts & Notebooks\n📓 demo.ipynb\n📄 examples/*.py"
    style.multiple: true
  }
}

simulation_layer: {
  label: "⚙️  SIMULATION LAYER"
  style.fill: "#fff4e1"
  style.stroke: "#ff6f00"
  style.stroke-width: 3
  
  environment: {
    label: "SimulationEnvironment\n🎯 compute_performance()\n💨 with_new_wind()"
    shape: rectangle
    style.bold: true
  }
  
  optimizer: {
    label: "Optimizer\n🎲 optimize_greedy()\n📊 sensitivity_analysis()"
    shape: rectangle
    style.bold: true
  }
}

component_layer: {
  label: "🧩  COMPONENT LAYER"
  style.fill: "#e8f5e9"
  style.stroke: "#2e7d32"
  style.stroke-width: 3
  
  array: {
    label: "ChillerArray\n📍 positions: (N×2)\n❄️ base_cop: 4.0"
    shape: rectangle
  }
  
  wind: {
    label: "WindVector\n💨 velocity: (vx, vy)\n🌡️ temp_k: 298.15"
    shape: rectangle
  }
  
  model: {
    label: "InteractionModel\n🔌 Pluggable"
    shape: rectangle
  }
}

model_layer: {
  label: "🧮  MODEL LAYER"
  style.fill: "#f3e5f5"
  style.stroke: "#6a1b9a"
  style.stroke-width: 3
  
  base: {
    label: "BaseInteractionModel\n(Abstract)"
    shape: hexagon
  }
  
  gaussian: {
    label: "GaussianPlumeModel\nσ = 1.2\n🌊 Dispersion"
    shape: rectangle
  }
}

core_layer: {
  label: "🏗️  CORE LAYER"
  style.fill: "#fce4ec"
  style.stroke: "#c2185b"
  style.stroke-width: 3
  
  configs: {
    label: "configs.py\n✅ Pydantic\n🛡️ Validation"
    shape: cylinder
  }
  
  constants: {
    label: "constants.py\n🔢 Defaults\n⚖️ Bounds"
    shape: cylinder
  }
}

# Relationships
user_layer.scripts -> simulation_layer.environment: invokes {style.stroke-width: 2}
user_layer.scripts -> simulation_layer.optimizer: invokes {style.stroke-width: 2}
simulation_layer.optimizer -> simulation_layer.environment: uses {style.stroke-dash: 3}

simulation_layer.environment -> component_layer.array: composes {style.stroke-width: 3}
simulation_layer.environment -> component_layer.wind: composes {style.stroke-width: 3}
simulation_layer.environment -> component_layer.model: composes {style.stroke-width: 3}

component_layer.model -> model_layer.base: implements {style.stroke-dash: 3}
model_layer.gaussian -> model_layer.base: extends {style.stroke-dash: 3}

component_layer.array -> core_layer.configs: validated by {style.stroke-dash: 3}
component_layer.wind -> core_layer.configs: validated by {style.stroke-dash: 3}
model_layer.gaussian -> core_layer.constants: uses {style.stroke-dash: 3}
"""

# ==============================================================================
# OPTION 3: PlantUML Component Diagram (Professional)
# ==============================================================================

COMPONENT_DIAGRAM_PLANTUML = """
@startuml Chiller Model Architecture

!theme vibrant
skinparam componentStyle rectangle
skinparam defaultTextAlignment center
skinparam wrapWidth 200
skinparam maxMessageSize 150

title Chiller Model - Component Architecture\n

package "User Interface Layer" <<Cloud>> #E1F5FF {
    [demo.ipynb] as notebook
    [examples/*.py] as examples
    [QUICK_START.py] as quickstart
}

package "Simulation Layer" <<Frame>> #FFF4E1 {
    component "SimulationEnvironment" as simenv #FFE082 {
        portin compute_performance
        portin with_new_wind
        portin with_new_model
    }
    
    component "Optimizer" as optimizer #FFE082 {
        portin optimize_greedy
        portin sensitivity_analysis
    }
}

package "Component Layer" <<Frame>> #E8F5E9 {
    component "ChillerArray" as array #A5D6A7 {
        [positions_m: NDArray]
        [base_cop: float]
        [alpha: float]
    }
    
    component "WindVector" as wind #A5D6A7 {
        [velocity_m_per_s]
        [ambient_temp_k]
        [direction]
    }
    
    interface "InteractionModel" as model_interface #81C784
}

package "Model Layer" <<Database>> #F3E5F5 {
    abstract BaseInteractionModel #CE93D8 {
        {abstract} compute_interaction_matrix()
        validate_matrix()
    }
    
    class GaussianPlumeModel #CE93D8 {
        - dispersion_coeff: float
        + compute_interaction_matrix()
        + compute_longitudinal_distances()
        + compute_lateral_distances()
    }
}

package "Core Layer" <<Node>> #FCE4EC {
    [configs.py\nPydantic] as configs
    [constants.py\nDefaults] as constants
    [ChillerSpec\nChillerState] as specs
}

' Relationships
notebook --> simenv : invokes
examples --> optimizer : invokes
optimizer ..> simenv : uses

simenv *-down- array : composes
simenv *-down- wind : composes
simenv *-down- model_interface : composes

model_interface <|.. BaseInteractionModel : implements
BaseInteractionModel <|-- GaussianPlumeModel : extends

array ..> configs : validates
wind ..> configs : validates
GaussianPlumeModel ..> constants : uses
array ..> specs : creates

note right of simenv
  **Composition Pattern**
  • Holds component instances
  • Orchestrates calculations
  • Immutable results
end note

note bottom of GaussianPlumeModel
  **Vectorized NumPy**
  • O(N²) space & time
  • No explicit loops
  • Fully parallelizable
end note

legend right
    |<#E1F5FF>  | User Interface Layer |
    |<#FFF4E1>  | Simulation Layer |
    |<#E8F5E9>  | Component Layer |
    |<#F3E5F5>  | Model Layer |
    |<#FCE4EC>  | Core Layer |
endlegend

@enduml
"""

# ==============================================================================
# OPTION 4: GraphViz DOT (Publication Quality)
# ==============================================================================

ARCHITECTURE_GRAPHVIZ = """
digraph ChillerModelArchitecture {
    // Graph settings
    rankdir=TB;
    compound=true;
    newrank=true;
    ranksep=1.2;
    nodesep=0.8;
    
    // Global node/edge defaults
    node [shape=box, style="rounded,filled", fontname="Arial", fontsize=11, height=0.6];
    edge [fontname="Arial", fontsize=10, arrowsize=0.8];
    
    // Subgraph styles
    graph [style="rounded,filled", fontname="Arial Bold", fontsize=13];
    
    // User Interface Layer
    subgraph cluster_ui {
        label="🖥️  USER INTERFACE LAYER";
        color="#0288d1";
        fillcolor="#e1f5ff";
        penwidth=3;
        
        scripts [label="User Scripts\n& Notebooks\n━━━━━━━━━\n📓 demo.ipynb\n📄 examples/*.py", 
                 fillcolor="#b3e5fc"];
    }
    
    // Simulation Layer
    subgraph cluster_simulation {
        label="⚙️  SIMULATION LAYER";
        color="#ff6f00";
        fillcolor="#fff4e1";
        penwidth=3;
        
        simenv [label="SimulationEnvironment\n━━━━━━━━━━━━━\n🎯 compute_performance()\n💨 with_new_wind()\n🔄 with_new_model()", 
                fillcolor="#ffe082", penwidth=2];
        optimizer [label="Optimizer\n━━━━━━━━━━━━━\n🎲 optimize_greedy()\n📊 sensitivity_analysis()", 
                   fillcolor="#ffe082", penwidth=2];
        
        {rank=same; simenv; optimizer;}
    }
    
    // Component Layer
    subgraph cluster_components {
        label="🧩  COMPONENT LAYER";
        color="#2e7d32";
        fillcolor="#e8f5e9";
        penwidth=3;
        
        array [label="ChillerArray\n━━━━━━━━━━━━━\n📍 positions_m: (N×2)\n❄️ base_cop: 4.0\n📉 alpha: 0.7", 
               fillcolor="#a5d6a7"];
        wind [label="WindVector\n━━━━━━━━━━━━━\n💨 velocity: (vx, vy)\n🌡️ temp_k: 298.15\n📐 direction, speed", 
              fillcolor="#a5d6a7"];
        model_interface [label="InteractionModel\n━━━━━━━━━━━━━\n🔌 Pluggable Interface\n🔁 Runtime Swappable", 
                         fillcolor="#a5d6a7", style="rounded,filled,dashed"];
        
        {rank=same; array; wind; model_interface;}
    }
    
    // Model Layer
    subgraph cluster_models {
        label="🧮  MODEL LAYER";
        color="#6a1b9a";
        fillcolor="#f3e5f5";
        penwidth=3;
        
        base [label="BaseInteractionModel\n━━━━━━━━━━━━━\n📜 Abstract Base Class\n⚡ compute_interaction_matrix()", 
              fillcolor="#ce93d8", shape=hexagon];
        gaussian [label="GaussianPlumeModel\n━━━━━━━━━━━━━\nσ dispersion: 1.2\n🌊 Plume Dispersion\n📐 Vectorized NumPy", 
                  fillcolor="#ba68c8", penwidth=2];
        
        {rank=same; base; gaussian;}
    }
    
    // Core Layer
    subgraph cluster_core {
        label="🏗️  CORE LAYER";
        color="#c2185b";
        fillcolor="#fce4ec";
        penwidth=3;
        
        configs [label="configs.py\n━━━━━━━━━━━━━\n✅ Pydantic Validation\n🛡️ Type Safety\n📏 SI Units", 
                 fillcolor="#f48fb1", shape=cylinder];
        constants [label="constants.py\n━━━━━━━━━━━━━\n🔢 Physical Constants\n📊 Default Values\n⚖️ Realistic Bounds", 
                   fillcolor="#f48fb1", shape=cylinder];
        specs [label="Data Structures\n━━━━━━━━━━━━━\n❄️ ChillerSpec\n📈 ChillerState\n📦 Results", 
               fillcolor="#f48fb1", shape=note];
        
        {rank=same; configs; constants; specs;}
    }
    
    // Inter-layer relationships
    scripts -> simenv [label="  invokes  ", color="#1976d2", penwidth=2];
    scripts -> optimizer [label="  invokes  ", color="#1976d2", penwidth=2];
    optimizer -> simenv [label="  uses  ", color="#757575", style=dashed];
    
    simenv -> array [label=" composes ", color="#2e7d32", penwidth=3];
    simenv -> wind [label=" composes ", color="#2e7d32", penwidth=3];
    simenv -> model_interface [label=" composes ", color="#2e7d32", penwidth=3];
    
    model_interface -> base [label="  implements  ", color="#6a1b9a", style=dashed];
    gaussian -> base [label="  extends  ", color="#6a1b9a", penwidth=2];
    simenv -> gaussian [label=" delegates ", color="#6a1b9a", style=dotted];
    
    array -> configs [label=" validated by ", color="#c2185b", style=dashed];
    wind -> configs [label=" validated by ", color="#c2185b", style=dashed];
    gaussian -> constants [label="  uses  ", color="#c2185b", style=dashed];
    array -> specs [label=" creates ", color="#c2185b", style=dashed];
    
    // Legend
    subgraph cluster_legend {
        label="Legend";
        color="#424242";
        fillcolor="#fafafa";
        
        leg1 [label="Solid = Strong dependency", shape=plaintext];
        leg2 [label="Dashed = Weak dependency", shape=plaintext];
        leg3 [label="Dotted = Delegation", shape=plaintext];
        
        {rank=same; leg1; leg2; leg3;}
    }
}
"""

if __name__ == "__main__":
    print("Enhanced Architecture Diagrams Generated!")
    print("\n" + "="*70)
    print("OPTION 1: Enhanced Mermaid (GitHub-compatible, interactive)")
    print("="*70)
    print(SYSTEM_ARCHITECTURE_STYLED)
    
    print("\n" + "="*70)
    print("OPTION 2: D2 Diagram Language (Modern, very pretty)")
    print("="*70)
    print("Install: brew install d2")
    print("Render: d2 architecture.d2 architecture.svg")
    
    print("\n" + "="*70)
    print("OPTION 3: PlantUML (Professional, publication-ready)")
    print("="*70)
    print("Install: brew install plantuml")
    print("Render: plantuml architecture.puml")
    
    print("\n" + "="*70)
    print("OPTION 4: GraphViz (Publication quality)")
    print("="*70)
    print("Install: brew install graphviz")
    print("Render: dot -Tsvg architecture.dot > architecture.svg")
