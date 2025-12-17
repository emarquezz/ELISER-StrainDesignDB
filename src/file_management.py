from pathlib import Path
import pandas as pd
import pickle

def get_files_dir(directory='ELISER-StrainDesignDB'):
    MAIN_DIR = Path.cwd()
    
    for parent in MAIN_DIR.parents:
            if parent.name == directory:
                BASE_DIR = parent
    INPUT_DIR = BASE_DIR / 'files' / 'Input'
    OUTPUT_DIR = BASE_DIR / 'files' / 'Output'
    return(BASE_DIR, INPUT_DIR, OUTPUT_DIR)



def check_save_file(dataframe, file_name, file_path, input_dir=False):
    BASE_DIR, INPUT_DIR, OUTPUT_DIR = get_files_dir()

    # Choose output directory
    base_output_dir = INPUT_DIR if input_dir else OUTPUT_DIR

    # Build full path
    file_output = base_output_dir / file_path / file_name
    file_output.parent.mkdir(parents=True, exist_ok=True)

    # Handle name collisions
    counter = 1
    while file_output.exists():
        file_output = (
            file_output.with_name(
                f"{file_output.stem}_new_v{counter}{file_output.suffix}"
            )
        )
        counter += 1

    # Save based on suffix
    suffix = file_output.suffix.lower()

    if suffix == ".json":
        dataframe.to_json(file_output)

    elif suffix == ".csv":
        dataframe.to_csv(file_output)

    elif suffix in {".pickle", ".pkl"}:
        dataframe.to_pickle(file_output)

    elif suffix == ".sav":
        with open(file_output, "wb") as f:
            pickle.dump(dataframe, f)

    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    print("Saved file in:", file_output)