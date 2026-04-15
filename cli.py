"""
Command-line interface for the Schwarzschild Geodesic Explorer.

Sub-commands
------------
  run      Integrate and plot a geodesic (custom parameters or a preset).
  presets  List all built-in presets.
  info     Print stats for a run without opening a plot window.
"""

from __future__ import annotations
import argparse

from config   import OrbitalParams, SolverConfig
import presets as preset_registry


def _preset_name(value: str) -> str:
    key = value.lower()
    if key not in preset_registry.PRESETS:
        available = ", ".join(preset_registry.PRESETS)
        raise argparse.ArgumentTypeError(
            f"Unknown preset '{value}'. Available: {available}"
        )
    return key


def _float_gt(min_value: float, *, inclusive: bool = False):
    def parse(value: str) -> float:
        try:
            f = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"Invalid float: {value!r}") from exc

        if inclusive:
            if f < min_value:
                raise argparse.ArgumentTypeError(
                    f"Must be ≥ {min_value}; got {f}."
                )
        else:
            if f <= min_value:
                raise argparse.ArgumentTypeError(
                    f"Must be > {min_value}; got {f}."
                )
        return f

    return parse


def _print_stats(sol, cfg=None) -> None:
    status = "★  PLUNGED INTO BLACK HOLE  ★" if sol.plunged else "Orbiting / Escaped"
    solver_name = cfg.solver if cfg else "—"
    print("=" * 44)
    print(f"  Solver      : {solver_name}")
    print(f"  Steps       : {sol.n_steps:,}")
    print(f"  Time        : {sol.elapsed_ms:.2f} ms")
    print(f"  Radius min  : {sol.r_min:.3f} rs")
    print(f"  Radius max  : {sol.r_max:.3f} rs")
    print(f"  Status      : {status}")
    print("=" * 44)


def _cmd_presets(_args: argparse.Namespace) -> None:
    """List all named presets."""
    print(f"\n{'Preset':<14}  Description")
    print("-" * 50)
    for name, desc in preset_registry.list_presets():
        print(f"  {name:<12}  {desc}")
    print()


def _cmd_run(args: argparse.Namespace) -> None:
    """Integrate a geodesic and display (or save) the plot."""
    import solver
 
    orbital, cfg = _resolve_params(args)
 
    print(f"\nRunning {cfg.solver} integrator …")
    sol = solver.run(orbital, cfg)
    _print_stats(sol, cfg)
 
    use_3d = getattr(args, "three_d", False)
    if use_3d:
        import plot3D as plotter
        saved_to = plotter.plot3d(
            sol,
            inclination_deg=args.inclination,
            save_path=args.save,
        )
    else:
        import plot as plotter
        saved_to = plotter.plot(sol, save_path=args.save)
 
    if saved_to:
        print(f"  Figure saved → {saved_to}")


def _cmd_info(args: argparse.Namespace) -> None:
    """Print stats without opening a plot window."""
    import solver

    orbital, cfg = _resolve_params(args)

    print(f"\nRunning {cfg.solver} integrator …")
    sol = solver.run(orbital, cfg)
    _print_stats(sol, cfg)


def _resolve_params(args: argparse.Namespace) -> tuple[OrbitalParams, SolverConfig]:
    """
    Return (OrbitalParams, SolverConfig) from either a preset name or
    individual CLI flags. Manual flags always override preset values
    """
    if args.preset:
        p = preset_registry.get(args.preset)
        base_orbital = p.orbital
        base_solver  = p.solver
    else:
        base_orbital = OrbitalParams()
        base_solver  = SolverConfig()

    orbital = OrbitalParams(
        r0_rs      = args.r0    if args.r0    is not None else base_orbital.r0_rs,
        speed_frac = args.speed if args.speed is not None else base_orbital.speed_frac,
        angle_deg  = args.angle if args.angle is not None else base_orbital.angle_deg,
    )
    cfg = SolverConfig(
        tau_max   = args.tau_max   if args.tau_max   is not None else base_solver.tau_max,
        step_size = args.step_size if args.step_size is not None else base_solver.step_size,
        solver    = args.solver    if args.solver    is not None else base_solver.solver,
    )
    return orbital, cfg


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schwarzschild",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # shared flags 
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--preset", type=_preset_name, metavar="NAME",
                        help="Named preset to use as base (case-insensitive).")
    shared.add_argument("--r0", type=_float_gt(0.0), metavar="RS",
                        help="Initial radius (units of rs).")
    shared.add_argument("--speed", type=_float_gt(0.0, inclusive=True), metavar="FRAC",
                        help="Speed fraction of circular speed (≥ 0).")
    shared.add_argument("--angle", type=float, metavar="DEG",
                        help="Launch angle in degrees (0=tangential).")
    shared.add_argument("--tau-max", type=_float_gt(0.0), metavar="TAU",
                        help="Proper time to integrate (> 0).")
    shared.add_argument("--step-size", type=_float_gt(0.0), metavar="H",
                        help="Step size / max_step for solver (> 0).")
    shared.add_argument("--solver", choices=["RK4", "RK45", "DOP853"],
                        help="Integrator to use.")

    # run 
    run_p = sub.add_parser("run", parents=[shared], help="Integrate and plot a geodesic.")
    run_p.add_argument("--save", metavar="PATH",
                       help="Save figure to file instead of displaying it.")
    run_p.add_argument("--3d", dest="three_d", action="store_true",
                       help="Render a 3D perspective plot instead of the default 2D polar plot.")
    run_p.add_argument("--inclination", type=float, default=30.0, metavar="DEG",
                       help="Tilt of the orbital plane for 3D view (degrees, default: 30).")
    run_p.set_defaults(func=_cmd_run)

    # info 
    info_p = sub.add_parser("info", parents=[shared], help="Print stats without opening a plot.")
    info_p.set_defaults(func=_cmd_info)

    # presets 
    presets_p = sub.add_parser("presets", help="List built-in presets.")
    presets_p.set_defaults(func=_cmd_presets)

    return parser
