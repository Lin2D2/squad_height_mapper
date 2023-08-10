import os

folder_name = "Yehorivka_AAS_v8"

mapper_data_files = list(sorted(filter(lambda o: o.lower().find("mapperoutput") != -1,
                                       os.listdir(folder_name)),
                                key=lambda name: int(name.split("_")[-2])))

with open(f"{folder_name}_mapperOutput.csv", "a+") as csv_file:
    hits_before = 0
    for file_name in mapper_data_files:
        file_name_split = file_name.split("_")
        print(f"converting chunk {int(file_name_split[-2])}/{len(mapper_data_files)}")
        with open(os.path.join(folder_name, file_name), "r") as file:
            raw_hits = file.readline().split(";")

        for index, raw_hit in enumerate(raw_hits):
            for raw_point in raw_hit.split("\\"):
                raw_point_split = raw_point.split("|")
                csv_file.write(f"{hits_before + index}," + ", ".join(raw_point_split) + "\n")

        hits_before += len(raw_hits) - 1
