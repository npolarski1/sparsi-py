import os
import shutil
import glob
from genlibdesc import generate_library_md

skill_names = ["sparsi-py-design", "sparsi-py-codegen"]
example_files = [
    "ticket_triager.py",
    "recipe_analyzer.py",
    "readme_quality.py",
    "stock_analyzer.py",
    "hn_topic_brief.py",
    "faithful_summary.py",
    "rag_basic.py",
]

def main():
    # 1. Copy README
    if os.path.exists("skill-src/README.md"):
        os.makedirs("skills", exist_ok=True)
        shutil.copy("skill-src/README.md", "skills/README.md")

    # 2. Process each skill
    lib_content = generate_library_md()
    
    for skill in skill_names:
        src_dir = os.path.join("skill-src", skill)
        dst_dir = os.path.join("skills", skill)
        os.makedirs(dst_dir, exist_ok=True)
        
        # Copy SKILL.md
        shutil.copy(os.path.join(src_dir, "SKILL.md"), os.path.join(dst_dir, "SKILL.md"))
        
        # Write library.md
        ref_dir = os.path.join(dst_dir, "references")
        os.makedirs(ref_dir, exist_ok=True)
        with open(os.path.join(ref_dir, "library.md"), "w", encoding="utf-8") as f:
            f.write(lib_content)
            
        # Copy examples
        ex_dst_root = os.path.join(ref_dir, "examples")
        os.makedirs(ex_dst_root, exist_ok=True)
        for ex_file in example_files:
            src_path = os.path.join("examples", ex_file)
            if os.path.exists(src_path):
                # Put in its own folder or just flat? Go uses folders.
                # Let's use folders for consistency with Go skill structure.
                ex_name = ex_file.replace(".py", "").replace("_", "-")
                ex_dir = os.path.join(ex_dst_root, ex_name)
                os.makedirs(ex_dir, exist_ok=True)
                shutil.copy(src_path, os.path.join(ex_dir, "main.py"))

    print("Skills generated successfully in /skills directory.")

if __name__ == "__main__":
    main()
