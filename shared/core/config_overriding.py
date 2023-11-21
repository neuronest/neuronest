from omegaconf import DictConfig


def override_config_forbidden_characters(config: DictConfig) -> DictConfig:
    for forbidden_character, replacement_character in zip(
        config.bigquery.dataset.forbidden_characters,
        config.bigquery.dataset.forbidden_characters_replacements,
    ):
        if forbidden_character not in config.bigquery.dataset.name:
            continue

        config.bigquery.dataset.name = config.bigquery.dataset.name.replace(
            forbidden_character, replacement_character
        )

    return config
