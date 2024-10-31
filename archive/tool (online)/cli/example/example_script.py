import pandas as pd

def main():
    print("Hello world!")
    
    df = pd.read_csv("example_data.csv")

    print(df)

if __name__ == "__main__":
    main()