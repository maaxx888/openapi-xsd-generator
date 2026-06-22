def get_user_selection(operations_info: dict) -> set[str]:
    while True:
        try:
            print("=" * 80)
            user_input = input(
                "Enter operation numbers to convert (comma-separated, e.g., '1,2,4')\n"
                "or press Enter to convert all: "
            ).strip()

            if not user_input:
                all_indices = set(operations_info["index_map"].keys())
                print(f"\nSelected all {len(all_indices)} operations.")
                return set(
                    operations_info["index_map"].values()
                )

            indices = set()
            for part in user_input.split(","):
                part = part.strip()
                if part:
                    idx = int(part)
                    if idx not in operations_info["index_map"]:
                        print(f"Error: Invalid operation number: {idx}")
                        break
                    indices.add(idx)
            else:
                selected_ops = {
                    operations_info["index_map"][idx] for idx in indices
                }
                print(f"\nSelected {len(selected_ops)} operations:")
                for op_id in sorted(selected_ops):
                    print(f"  - {op_id}")
                return selected_ops

        except ValueError:
            print("Error: Please enter valid numbers separated by commas.")
            continue
