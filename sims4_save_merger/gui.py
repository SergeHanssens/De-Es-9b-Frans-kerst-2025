"""
GUI for Sims 4 Save Merger

A user-friendly graphical interface for merging Sims 4 save files.
Built with tkinter for cross-platform compatibility.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional
import threading
import os
import traceback

from .merger import Sims4SaveMerger, MergeResult, MergeStrategy


class Sims4MergerGUI:
    """Main GUI application for the Sims 4 Save Merger"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sims 4 Save Merger")
        self.root.geometry("800x700")
        self.root.minsize(700, 600)

        # Set style
        self.style = ttk.Style()
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        self.style.configure('Header.TLabel', font=('Arial', 11, 'bold'))
        self.style.configure('Info.TLabel', font=('Arial', 9))

        # Variables
        self.newer_path = tk.StringVar()
        self.older_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.progress_var = tk.IntVar(value=0)
        self.status_var = tk.StringVar(value="Selecteer beide save bestanden om te beginnen")

        # Merger instance
        self.merger: Optional[Sims4SaveMerger] = None
        self.files_loaded = False

        # Build UI
        self._create_widgets()

        # Default paths (common Sims 4 save location)
        self._set_default_paths()

    def _set_default_paths(self):
        """Set default path to Sims 4 saves folder"""
        if os.name == 'nt':  # Windows
            documents = Path.home() / "Documents"
            sims4_saves = documents / "Electronic Arts" / "The Sims 4" / "saves"
        else:  # Linux/Mac
            documents = Path.home() / "Documents"
            sims4_saves = documents / "Electronic Arts" / "The Sims 4" / "saves"

        if sims4_saves.exists():
            self.default_dir = str(sims4_saves)
        else:
            self.default_dir = str(Path.home())

    def _create_widgets(self):
        """Create all GUI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="🎮 Sims 4 Save Merger",
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, pady=(0, 5))

        subtitle = ttk.Label(
            main_frame,
            text="Combineer twee save bestanden tot één werkend bestand",
            style='Info.TLabel'
        )
        subtitle.grid(row=1, column=0, pady=(0, 15))

        # File selection frame
        files_frame = ttk.LabelFrame(main_frame, text="Save Bestanden", padding="10")
        files_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        files_frame.columnconfigure(1, weight=1)

        # Newer save file
        ttk.Label(files_frame, text="Nieuwere Save:", style='Header.TLabel').grid(
            row=0, column=0, sticky="w", pady=5
        )
        ttk.Label(
            files_frame,
            text="(Basis bestand - Sims zijn ouder, maar data ontbreekt)",
            style='Info.TLabel'
        ).grid(row=0, column=1, sticky="w", padx=5)

        newer_frame = ttk.Frame(files_frame)
        newer_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        newer_frame.columnconfigure(0, weight=1)

        ttk.Entry(newer_frame, textvariable=self.newer_path).grid(
            row=0, column=0, sticky="ew", padx=(0, 5)
        )
        ttk.Button(
            newer_frame,
            text="Bladeren...",
            command=self._browse_newer
        ).grid(row=0, column=1)

        # Older save file
        ttk.Label(files_frame, text="Oudere Save:", style='Header.TLabel').grid(
            row=2, column=0, sticky="w", pady=5
        )
        ttk.Label(
            files_frame,
            text="(Bron voor ontbrekende data - gebouwen, objecten, etc.)",
            style='Info.TLabel'
        ).grid(row=2, column=1, sticky="w", padx=5)

        older_frame = ttk.Frame(files_frame)
        older_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        older_frame.columnconfigure(0, weight=1)

        ttk.Entry(older_frame, textvariable=self.older_path).grid(
            row=0, column=0, sticky="ew", padx=(0, 5)
        )
        ttk.Button(
            older_frame,
            text="Bladeren...",
            command=self._browse_older
        ).grid(row=0, column=1)

        # Output file
        ttk.Label(files_frame, text="Output Bestand:", style='Header.TLabel').grid(
            row=4, column=0, sticky="w", pady=5
        )
        ttk.Label(
            files_frame,
            text="(Het samengevoegde resultaat)",
            style='Info.TLabel'
        ).grid(row=4, column=1, sticky="w", padx=5)

        output_frame = ttk.Frame(files_frame)
        output_frame.grid(row=5, column=0, columnspan=3, sticky="ew")
        output_frame.columnconfigure(0, weight=1)

        ttk.Entry(output_frame, textvariable=self.output_path).grid(
            row=0, column=0, sticky="ew", padx=(0, 5)
        )
        ttk.Button(
            output_frame,
            text="Bladeren...",
            command=self._browse_output
        ).grid(row=0, column=1)

        # Analysis button
        ttk.Button(
            main_frame,
            text="📊 Analyseer Bestanden",
            command=self._analyze_files
        ).grid(row=3, column=0, pady=10)

        # Info frame
        self.info_frame = ttk.LabelFrame(main_frame, text="Analyse Resultaat", padding="10")
        self.info_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        main_frame.rowconfigure(4, weight=1)
        self.info_frame.columnconfigure(0, weight=1)
        self.info_frame.rowconfigure(0, weight=1)

        # Info text area
        self.info_text = tk.Text(
            self.info_frame,
            height=12,
            wrap=tk.WORD,
            font=('Consolas', 10)
        )
        self.info_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.info_frame, command=self.info_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.info_text.config(yscrollcommand=scrollbar.set)

        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")

        ttk.Label(progress_frame, textvariable=self.status_var).grid(
            row=1, column=0, pady=(5, 0)
        )

        # Merge button
        self.merge_button = ttk.Button(
            main_frame,
            text="🔀 Samenvoegen",
            command=self._start_merge,
            state='disabled'
        )
        self.merge_button.grid(row=6, column=0, pady=10)

        # Help text
        help_text = """
Instructies:
1. Selecteer de NIEUWERE save (basis bestand met de actuele Sim-voortgang)
2. Selecteer de OUDERE save (bevat de ontbrekende gebouwen/objecten)
3. Klik op "Analyseer Bestanden" om te zien wat er samengevoegd kan worden
4. Kies een locatie voor het output bestand
5. Klik op "Samenvoegen" om het gecombineerde save bestand te maken

Tip: Maak altijd een backup van je originele saves voordat je begint!
        """
        help_label = ttk.Label(main_frame, text=help_text.strip(), style='Info.TLabel')
        help_label.grid(row=7, column=0, pady=(10, 0))

    def _browse_newer(self):
        """Browse for newer save file"""
        path = filedialog.askopenfilename(
            title="Selecteer Nieuwere Save",
            initialdir=self.default_dir,
            filetypes=[
                ("Sims 4 Save", "*.save"),
                ("Alle bestanden", "*.*")
            ]
        )
        if path:
            self.newer_path.set(path)
            self._suggest_output_name()

    def _browse_older(self):
        """Browse for older save file"""
        path = filedialog.askopenfilename(
            title="Selecteer Oudere Save",
            initialdir=self.default_dir,
            filetypes=[
                ("Sims 4 Save", "*.save"),
                ("Alle bestanden", "*.*")
            ]
        )
        if path:
            self.older_path.set(path)

    def _browse_output(self):
        """Browse for output file location"""
        path = filedialog.asksaveasfilename(
            title="Opslaan Als",
            initialdir=self.default_dir,
            defaultextension=".save",
            filetypes=[
                ("Sims 4 Save", "*.save"),
                ("Alle bestanden", "*.*")
            ]
        )
        if path:
            self.output_path.set(path)

    def _suggest_output_name(self):
        """Suggest an output filename based on input"""
        if self.newer_path.get() and not self.output_path.get():
            newer = Path(self.newer_path.get())
            suggested = newer.parent / f"{newer.stem}_merged.save"
            self.output_path.set(str(suggested))

    def _update_progress(self, message: str, percent: int):
        """Update progress bar and status (thread-safe)"""
        self.root.after(0, lambda: self._do_update_progress(message, percent))

    def _do_update_progress(self, message: str, percent: int):
        """Actually update the progress (runs on main thread)"""
        self.status_var.set(message)
        if percent >= 0:
            self.progress_var.set(percent)

    def _analyze_files(self):
        """Analyze the selected save files"""
        if not self.newer_path.get() or not self.older_path.get():
            messagebox.showerror(
                "Fout",
                "Selecteer beide save bestanden eerst."
            )
            return

        # Verify files exist
        if not Path(self.newer_path.get()).exists():
            messagebox.showerror("Fout", "Nieuwere save bestand niet gevonden.")
            return

        if not Path(self.older_path.get()).exists():
            messagebox.showerror("Fout", "Oudere save bestand niet gevonden.")
            return

        self.merge_button.config(state='disabled')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, "Bestanden laden en analyseren...\n")

        # Run in thread
        thread = threading.Thread(target=self._do_analysis)
        thread.start()

    def _do_analysis(self):
        """Perform the analysis (runs in thread)"""
        try:
            self.merger = Sims4SaveMerger(self._update_progress)
            newer_stats, older_stats = self.merger.load_files(
                Path(self.newer_path.get()),
                Path(self.older_path.get())
            )

            comparison = self.merger.get_comparison_summary()
            mergeable = self.merger.get_mergeable_resources()

            # Format results
            result = self._format_analysis(newer_stats, older_stats, comparison, mergeable)

            self.root.after(0, lambda: self._show_analysis_result(result, True))

        except Exception as e:
            # Get detailed error information
            error_details = traceback.format_exc()
            error_msg = f"""Fout bij analyseren: {str(e)}

MOGELIJKE OORZAKEN:
1. Het bestand is geen geldig Sims 4 save bestand
2. Het bestand is beschadigd of incompleet
3. Het bestand gebruikt een niet-ondersteund formaat

DETAILS:
{error_details}

TIP: Probeer de debug tool om meer informatie te krijgen:
  python -m sims4_save_merger.debug_save "{self.newer_path.get()}"
"""
            self.root.after(0, lambda: self._show_analysis_result(error_msg, False))

    def _format_analysis(self, newer_stats, older_stats, comparison, mergeable) -> str:
        """Format the analysis results for display"""
        lines = []
        lines.append("=" * 60)
        lines.append("ANALYSE RESULTAAT")
        lines.append("=" * 60)
        lines.append("")

        lines.append("📁 NIEUWERE SAVE (basis):")
        lines.append(f"   Bestand: {Path(newer_stats['filepath']).name}")
        lines.append(f"   Resources: {newer_stats['resource_count']}")
        lines.append(f"   Grootte: {newer_stats['total_size'] / 1024 / 1024:.2f} MB")
        lines.append("")

        lines.append("📁 OUDERE SAVE (bron):")
        lines.append(f"   Bestand: {Path(older_stats['filepath']).name}")
        lines.append(f"   Resources: {older_stats['resource_count']}")
        lines.append(f"   Grootte: {older_stats['total_size'] / 1024 / 1024:.2f} MB")
        lines.append("")

        lines.append("=" * 60)
        lines.append("VERGELIJKING")
        lines.append("=" * 60)
        lines.append("")

        lines.append(f"✅ Identiek in beide:     {comparison['same']}")
        lines.append(f"🔄 Verschillend:          {comparison['different']}")
        lines.append(f"📌 Alleen in nieuwere:    {comparison['only_in_newer']}")
        lines.append(f"📌 Alleen in oudere:      {comparison['only_in_older']}")
        lines.append("")

        if comparison['only_older_by_type']:
            lines.append("Resources die toegevoegd kunnen worden (per type):")
            for type_name, count in sorted(comparison['only_older_by_type'].items()):
                lines.append(f"   • {type_name}: {count}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("MERGE PREVIEW")
        lines.append("=" * 60)
        lines.append("")

        total_new = newer_stats['resource_count']
        total_to_add = comparison['resources_to_add']
        total_merged = total_new + total_to_add

        lines.append(f"Het samengevoegde bestand zal bevatten:")
        lines.append(f"   • {total_new} resources van de nieuwere save")
        lines.append(f"   • {total_to_add} resources toegevoegd van de oudere save")
        lines.append(f"   • {total_merged} resources totaal")
        lines.append("")

        if total_to_add > 0:
            lines.append("✅ Klaar om samen te voegen!")
        else:
            lines.append("ℹ️ Geen ontbrekende resources gevonden in de oudere save.")

        return "\n".join(lines)

    def _show_analysis_result(self, result: str, success: bool):
        """Show analysis result in the info text area"""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, result)

        if success:
            self.files_loaded = True
            self.merge_button.config(state='normal')
        else:
            self.files_loaded = False
            self.merge_button.config(state='disabled')

    def _start_merge(self):
        """Start the merge process"""
        if not self.files_loaded or not self.merger:
            messagebox.showerror("Fout", "Analyseer de bestanden eerst.")
            return

        if not self.output_path.get():
            messagebox.showerror("Fout", "Selecteer een output bestand.")
            return

        # Confirm
        if not messagebox.askyesno(
            "Bevestigen",
            f"Wil je de bestanden samenvoegen en opslaan naar:\n{self.output_path.get()}?"
        ):
            return

        self.merge_button.config(state='disabled')

        # Run in thread
        thread = threading.Thread(target=self._do_merge)
        thread.start()

    def _do_merge(self):
        """Perform the merge (runs in thread)"""
        try:
            result = self.merger.merge(
                Path(self.output_path.get()),
                MergeStrategy.NEWER_BASE_ADD_MISSING
            )

            self.root.after(0, lambda: self._show_merge_result(result))

        except Exception as e:
            error_msg = f"Fout bij samenvoegen: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Fout", error_msg))
            self.root.after(0, lambda: self.merge_button.config(state='normal'))

    def _show_merge_result(self, result: MergeResult):
        """Show merge result"""
        self.merge_button.config(state='normal')

        if result.success:
            msg = f"""Samenvoegen succesvol!

📊 Resultaat:
• Resources van nieuwere save: {result.resources_from_newer}
• Resources van oudere save: {result.resources_from_older}
• Totaal resources: {result.resources_total}

📁 Opgeslagen naar:
{result.output_file}
"""
            if result.warnings:
                msg += "\n⚠️ Waarschuwingen:\n"
                msg += "\n".join(f"• {w}" for w in result.warnings)

            messagebox.showinfo("Succes", msg)

            # Update info text
            self.info_text.insert(tk.END, "\n\n" + "=" * 60 + "\n")
            self.info_text.insert(tk.END, "MERGE VOLTOOID\n")
            self.info_text.insert(tk.END, "=" * 60 + "\n\n")
            self.info_text.insert(tk.END, msg)

        else:
            msg = "Samenvoegen mislukt.\n\nFouten:\n"
            msg += "\n".join(f"• {e}" for e in result.errors)
            messagebox.showerror("Fout", msg)

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


def main():
    """Entry point for the GUI application"""
    app = Sims4MergerGUI()
    app.run()


if __name__ == '__main__':
    main()
