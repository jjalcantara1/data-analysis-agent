import json
import pandas as pd
import numpy as np
import re

def numpy_encoder(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, pd.Series) or isinstance(obj, pd.Index):
        return obj.tolist()
    return json.JSONEncoder.default(obj)

def _process_markdown_and_save_charts(markdown_text: str, output_dir: str) -> str:
    """
    Finds placeholder text (**[Chart Title]**) created by the LLM
    and replaces it with a Markdown link to the file saved on disk
    (e.g., ![Chart Title](charts/chart_title.png)).
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    placeholder_pattern = r'\*\*\[(.+?)\]\*\*'

    def replace_placeholder_with_link(match):
        chart_title = match.group(1).strip()

        safe_filename = re.sub(r'\W+', '_', chart_title).lower() + ".png"

        relative_path = os.path.join(os.path.basename(output_dir), safe_filename)

        return f'![{chart_title}]({relative_path})'

    cleaned_markdown = re.sub(placeholder_pattern, replace_placeholder_with_link, markdown_text)

    corrupted_base64_pattern = r'!\[.*?\]\(data:image/png;base64,.*?\)'

    def replace_corrupted_tag(match):
        return "**[Visualization File Missing - Corrupted Link]**"

    cleaned_markdown = re.sub(corrupted_base64_pattern, replace_corrupted_tag, cleaned_markdown, flags=re.S)

    note = "\n\n---\n\n**NOTE:** All charts are generated and saved as separate PNG files in the `./charts/` directory. The report refers to them by their title (e.g., ![Gender Distribution](charts/gender_distribution.png))."

    return cleaned_markdown + note
