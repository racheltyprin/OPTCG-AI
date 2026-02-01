# To reset the data run the following commands in terminal:
## Vegapull commands:
cargo install vegapull

git clone https://github.com/coko7/vegapull.git

cd vegapull

cargo build --release

vega pull all
    (use selections: english, packs, y, N)


## Consolidation commands:

python3 consolidate.py consolidate

(use "python3 consolidate.py reset" to check reset)