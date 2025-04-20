from pathlib import Path
from datetime import datetime as dt
import click

from src.personal_knowledge_assistant.pipelines.notion_to_vector import notion_to_vector_pipeline


@click.command()
@click.option(
    "--no-cache", is_flag=True, default=False, help="Disable caching for the pipeline run."
)
def main(no_cache: bool):
    pipeline_args = {
        "enable_cache": not no_cache,
        "config_path": Path("configs/notion_to_vector.yaml"),
        "run_name": f"notion_to_vector_run_{dt.now().strftime('%Y_%m_%d_%H_%M_%S')}"
    }

    notion_to_vector_pipeline.with_options(**pipeline_args)()


if __name__ == "__main__":
    main()