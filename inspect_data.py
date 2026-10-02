import pandas as pd

def analyze_and_convert(excel_filename: str, csv_filename: str):
    print(f"Loading '{excel_filename}'...")
    
    # 1. Read the Excel file
    df = pd.read_excel(excel_filename)
    
    # 2. Print the column names for analysis
    print("\n--- Column Names in Dataset ---")
    for col in df.columns:
        print(f"- {col}")
        
    # 3. Convert and save it as a CSV file
    df.to_csv(csv_filename, index=False)
    print(f"\nSuccessfully converted the dataset to '{csv_filename}'!")

if __name__ == "__main__":
    # Replace with your actual file names
    analyze_and_convert("Anuvaad_INDB_2024.11.xlsx", "indb_full.csv")