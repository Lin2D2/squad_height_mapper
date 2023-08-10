import os

folder_name = "Yehorivka_AAS_v8"

mapper_data_files = list(sorted(filter(lambda o: o.lower().find("mapperoutput") != -1,
                                       os.listdir(folder_name)),
                                key=lambda name: int(name.split("_")[-2])))

with open(f"{folder_name}_mapperOutput.csv", "a+") as csv_file:
    csv_file.write("id,location_x,location_y,location_z,impact_normal_x,impact_normal_y,impact_normal_z,"
                   "hit_actor,hit_component,material\n")
    hits_before = 0
    for file_name in mapper_data_files:
        file_name_split = file_name.split("_")
        print(f"converting chunk {int(file_name_split[-2])}/{len(mapper_data_files)}")
        with open(os.path.join(folder_name, file_name), "r") as file:
            raw_hits = file.readline().split(";")

        for index, raw_hit in enumerate(raw_hits):
            for raw_point in raw_hit.split("\\"):
                raw_point_split = raw_point.split("|")
                csv_file.write(f"{hits_before + index}," +
                               ",".join(raw_point_split[0].split(" ")) + "," +
                               ",".join(raw_point_split[1].split(" ")) + "," +
                               '"' + raw_point_split[2].lower() + '"' + "," +
                               '"' + raw_point_split[3].lower() + '"' + "," +
                               '"' + raw_point_split[4].lower() + '"' + "\n")

        hits_before += len(raw_hits) - 1
