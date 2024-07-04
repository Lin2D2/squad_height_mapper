import os
import os.path
import math
import json
import random

from time import perf_counter

import numpy as np
import sqlite3 as sq
import pandas as pd

from PIL import Image

from debug_view import DebugView

# TODOs
# P12 line of site pull coordinates and direction from game and render overlay with site lines
# P1 height lines
# P4 roads
# P5 buildings
# P6 (campsites)
# P3 color map for heights see atlas
# P7 not walkable terrain ist marked
# P2 height liens closer together when terrain is steep


# noinspection SpellCheckingInspection
building_keys = {"house", "apartment", "barn", "tower", "factory", "industrial", "office", "roof", "shed", "building",
                 "urbres", "garrage", "garage", "urbcnt", "market", "shop", "tent", "residential", "mosque",
                 "construction", "gassilo", "corrugatedcover"}
# noinspection SpellCheckingInspection
bridge_keys = {"bridge"}
# noinspection SpellCheckingInspection
street_keys = {"street", "road", "bridge"}
# noinspection SpellCheckingInspection
main_road_keys = {"main", "edgeline"}
# noinspection SpellCheckingInspection
road_keys = {"centerline", "doublelane", "crossing", "plain", "road"}  # TODO crossing seperate
# noinspection SpellCheckingInspection
small_road_keys = {"dirtgravel"}
# noinspection SpellCheckingInspection
train_track_key = "track"
# noinspection SpellCheckingInspection
grass_key = "grass"
# noinspection SpellCheckingInspection
dirt_key = "dirt"
# noinspection SpellCheckingInspection
mud_key = "mud"
# noinspection SpellCheckingInspection
trees_key = "tree"
# noinspection SpellCheckingInspection
water_key = "water"  # TODO find better way

# values m or cm ? unreal engine
height_line_step_size = 1000  # 2500 = 25m
# TODO write height in the line example: ----- 2000 ------

default_color = 255, 253, 238

height_line_color = 128, 128, 128

grass_color = 209, 240, 197
dirt_color = default_color
trees_color = 181, 194, 112
water_color = 210, 232, 250
mud_color = 202, 203, 134
bridge_color = 255, 255, 0  # TODO find bridge color
main_road_color = 255, 109, 44
road_color = 255, 166, 39
# side_road_color = 255, 255, 255
small_road_color = 230, 160, 120
train_track_color = 102, 102, 102
building_color = 168, 168, 168

corn_color = 200, 200, 80
wheat_color = 225, 225, 80


# TODO have an point tag, set when writing into database, for example tag: street, building, terrain usw.
# TODO maybe also find way to speed up height lines
# TODO find if there is a faster in memory db end goal is for one use so db is no use


class Mapper:
    def __init__(self, folder_name,
                 in_memory_bool=False,
                 generate_bool=True,
                 generate__height_lines_bool=True,
                 debug_view_bool=False,
                 draw_progress=False):
        self.debug_view_bool = debug_view_bool
        self.generate_bool = generate_bool
        self.draw_progress = draw_progress
        self.generate_height_lines = generate__height_lines_bool
        self.height_to_colour = lambda height, reduction: int((height + self.z_min * -1) /
                                                              ((self.z_min * -1 + self.z_max) / reduction))
        # noinspection SpellCheckingInspection
        mapper_data_file = list(filter(lambda o: o.lower().find("mapperoutput") != -1, os.listdir(folder_name)))[0]
        instanced_data_files = list(filter(lambda o: o.lower().find("instanced") != -1, os.listdir(folder_name)))
        reference_image = os.path.join(folder_name, list(filter(lambda o: o.lower().find(".bmp") != -1,
                                                                os.listdir(folder_name)))[0])
        print(f"loading files from folder: {folder_name}")
        print(f"parsing data")
        start_time = perf_counter()

        self.point_data = pd.read_csv(os.path.join(folder_name, mapper_data_file))

        self.point_data_landscape = self.point_data["hit_actor"].str.match("landscape")

        self.resolution = int(math.sqrt(self.point_data["id"][self.point_data_landscape].max())) + 1
        self.x_min = self.point_data["location_x"][self.point_data_landscape].min()
        self.x_max = self.point_data["location_x"][self.point_data_landscape].max()
        self.y_min = self.point_data["location_y"][self.point_data_landscape].min()
        self.y_max = self.point_data["location_y"][self.point_data_landscape].max()
        self.z_min = self.point_data["location_z"][self.point_data_landscape].min()
        self.z_max = self.point_data["location_z"][self.point_data_landscape].max()

        # # -----------
        # # TODO remove below also replace with csv and pandas
        #
        # db_exist = os.path.exists(f"height_mapper_{folder_name}.db")
        #
        # if in_memory_bool:
        #     print(f"running database only in memory")
        #     self.database = sq.connect(":memory:")
        # else:
        #     self.database = sq.connect(f"height_mapper_{folder_name}.db")
        # self.database_cursor = self.database.cursor()
        # self.database_cursor.execute("PRAGMA JOURNAL_MODE = OFF")
        # self.database_cursor.execute("PRAGMA SYNCHRONOUS = OFF")
        # self.database_cursor.execute("PRAGMA LOCKING_MODE = EXCLUSIVE")
        #
        # if not db_exist or in_memory_bool:
        #     self.database_cursor.execute("CREATE TABLE objects_meta("
        #                                  "reference TEXT,"
        #                                  "max_extend_x FLOAT,"
        #                                  "max_extend_y FLOAT,"
        #                                  "max_extend_z FLOAT,"
        #                                  "min_extend_x FLOAT,"
        #                                  "min_extend_y FLOAT,"
        #                                  "min_extend_z FLOAT"
        #                                  ")")
        #     self.database_cursor.execute("CREATE TABLE objects("
        #                                  "reference TEXT,"
        #                                  "location_x FLOAT,"
        #                                  "location_y FLOAT,"
        #                                  "location_z FLOAT,"
        #                                  "scale_x FLOAT,"
        #                                  "scale_y FLOAT,"
        #                                  "scale_z FLOAT"
        #                                  ")")
        #
        #     for file_name in instanced_data_files:
        #         char = '"'
        #         print(file_name)
        #         with open(os.path.join(folder_name, file_name), "r") as file:
        #             data = json.load(file)
        #             reference_object = data['name'].split(' ')[-1]
        #             database_string = f"INSERT INTO objects_meta " \
        #                               f"VALUES({char}{reference_object}{char}, " \
        #                               f"{', '.join([e.split('=')[-1] for e in data['max'].split(' ')])}, " \
        #                               f"{', '.join([e.split('=')[-1] for e in data['min'].split(' ')])})"
        #             self.database_cursor.execute(database_string)
        #             self.database.commit()
        #             for point in data["data"]:
        #                 point_split = point.split("|")
        #                 database_string = f"INSERT INTO objects " \
        #                                   f"VALUES({char}{reference_object}{char}, " \
        #                                   f"{', '.join([e.split('=')[-1] for e in point_split[0].split(' ')])}, " \
        #                                   f"{', '.join([e.split('=')[-1] for e in point_split[1].split(' ')])})"
        #                 self.database_cursor.execute(database_string)
        #             self.database.commit()
        #
        # else:
        #     print(f"database {folder_name} already exist skipping")
        #
        # # ---------------

        # self.x_extend = abs(self.x_max) + abs(self.x_min)
        # self.y_extend = abs(self.y_max) + abs(self.y_min)
        #
        # if self.x_extend != self.y_extend:
        #     print("::WARNING:: extends not equal")
        # TODO read from file
        self.step_size = 100

        print(f"parsing took: {perf_counter() - start_time}")
        start_time = perf_counter()

        if self.draw_progress:
            self.debug_view = DebugView(np.empty((self.resolution, self.resolution, 3)),
                                        self.resolution,
                                        self.database_cursor,
                                        reference_image)

        if self.generate_bool:
            self.image = self.generate_image()
            self.image.save("tmp.png")
        else:
            self.image = Image.open("tmp.png")

        print(f"generating took: {perf_counter() - start_time}")

        # TODO add new instanced objects to debug view

        if self.debug_view_bool:
            self.debug_view = DebugView(self.image.tobytes(),
                                        self.resolution,
                                        self.database_cursor,
                                        reference_image)
            self.debug_view.run()

    @staticmethod
    def all_equal(iterator):
        iterator = iter(iterator)
        try:
            first = next(iterator)
        except StopIteration:
            return True
        return all(first == x for x in iterator)

    @staticmethod
    def num_equal(first, iterator):
        return sum(1 if first == x else 0 for x in iterator)

    @staticmethod
    def find_neighbours(center_point_id: int, points: dict, resolution: int):
        row_num = center_point_id // resolution
        col_num = center_point_id % resolution
        neighbours = [
            points.get((row_num - 1) * resolution + col_num - 1),
            points.get((row_num - 1) * resolution + col_num),
            points.get((row_num - 1) * resolution + col_num + 1),
            points.get(center_point_id - 1),
            points.get(center_point_id + 1),
            points.get((row_num + 1) * resolution + col_num - 1),
            points.get((row_num + 1) * resolution + col_num),
            points.get((row_num + 1) * resolution + col_num + 1),
        ]
        return filter(lambda e: e is not None, neighbours)

    def get_index_from_coordinates(self, x_a, x_i, y_a, y_i):
        # TODO add rotation
        if x_a > 0:
            x_start = (abs(x_a) + abs(self.x_min)) // self.step_size
        else:
            x_start = (abs(self.x_min) - abs(x_a)) // self.step_size
        if x_i > 0:
            x_end = (abs(x_i) + abs(self.x_min)) // self.step_size
        else:
            x_end = (abs(self.x_min) - abs(x_i)) // self.step_size
        if y_a > 0:
            y_start = (abs(y_a) + abs(self.y_min)) // self.step_size
        else:
            y_start = (abs(self.y_min) - abs(y_a)) // self.step_size
        if y_i > 0:
            y_end = (abs(y_i) + abs(self.y_min)) // self.step_size
        else:
            y_end = (abs(self.y_min) - abs(y_i)) // self.step_size

        # just sets to middle of object
        # TODO in future return start and end points
        if x_start == x_end:
            x = x_start
        else:
            x = (x_end - x_start) // 2 + x_start
        if y_start == y_end:
            y = y_start
        else:
            y = (y_end - y_start) // 2 + y_start

        # if location_x > 0:
        #     x = int((abs(location_x) + abs(self.x_min)) / self.step_size)
        # else:
        #     x = int((abs(self.x_min) - abs(location_x)) / self.step_size)
        # if location_y > 0:
        #     y = int((abs(location_y) + abs(self.y_min)) / self.step_size)
        # else:
        #     y = int((abs(self.y_min) - abs(location_y)) / self.step_size)

        return int(y * self.resolution + x)

    def generate_from_db(self):  # TODO use find_neighbours for house trees and roads as well
        image = np.full((self.resolution * self.resolution, 3), default_color, dtype=np.uint8)

        # Terrain
        start = perf_counter()
        image[self.point_data["id"][self.point_data["material"].str.contains(grass_key) & self.point_data_landscape]] = grass_color

        if self.draw_progress:
            self.debug_view.render_image(image.tobytes())

        print(f"terrain grass took: {perf_counter() - start}")

        # start = perf_counter()
        #
        # instanced_object_query = self.database_cursor.execute("SELECT * FROM objects_meta").fetchall()
        #
        # print(f"instanced_object query took: {perf_counter() - start}")
        # start = perf_counter()
        #
        # for reference, max_extend_x, max_extend_y, max_extend_z, min_extend_x, min_extend_y, min_extend_z in instanced_object_query:
        #     # TODO maybe draw rocks some where else
        #     if any(key in reference.lower() for key in ["deco", "rock", "grass", "cattails", "foxglove"]):
        #         continue
        #     # print(f"instanced_object: {reference}")
        #     char = '"'
        #     instanced_objects_query = self.database_cursor.execute(
        #         f"SELECT * FROM objects WHERE reference = {char}{reference}{char}").fetchall()
        #     for reference_object, location_x, location_y, location_z, scale_x, scale_y, scale_z in instanced_objects_query:
        #         index = self.get_index_from_coordinates(location_x + max_extend_x * scale_x,
        #                                                 location_x + min_extend_x * scale_x,
        #                                                 location_y + max_extend_y * scale_y,
        #                                                 location_y + min_extend_y * scale_y)
        #         # image.put(index * 3 + 0, trees_color[0])
        #         # image.put(index * 3 + 1, trees_color[1])
        #         # image.put(index * 3 + 2, trees_color[2])
        #         if "corn" in reference.lower():
        #             image.put(index * 3 + 0, corn_color[0])
        #             image.put(index * 3 + 1, corn_color[1])
        #             image.put(index * 3 + 2, corn_color[2])
        #         elif "wheat" in reference.lower():
        #             image.put(index * 3 + 0, wheat_color[0])
        #             image.put(index * 3 + 1, wheat_color[1])
        #             image.put(index * 3 + 2, wheat_color[2])
        #         else:
        #             # trees
        #             # image.put(index * 3 + 0, 255)
        #             # image.put(index * 3 + 1, 0)
        #             # image.put(index * 3 + 2, 0)
        #             # TODO find clean solution
        #             # TODO generate forest patches
        #             row_num = index // self.resolution
        #             col_num = index % self.resolution
        #             try:
        #                 left_up = (row_num - 1) * self.resolution + col_num - 1
        #                 image.put(left_up * 3 + 0, trees_color[0] + 20)
        #                 image.put(left_up * 3 + 1, trees_color[1] + 20)
        #                 image.put(left_up * 3 + 2, trees_color[2] + 20)
        #             except IndexError:
        #                 pass
        #
        #             try:
        #                 up = (row_num - 1) * self.resolution + col_num
        #                 image.put(up * 3 + 0, trees_color[0] + 10)
        #                 image.put(up * 3 + 1, trees_color[1] + 10)
        #                 image.put(up * 3 + 2, trees_color[2] + 10)
        #             except IndexError:
        #                 pass
        #
        #             try:
        #                 right_up = (row_num - 1) * self.resolution + col_num + 1
        #                 image.put(right_up * 3 + 0, trees_color[0] + 20)
        #                 image.put(right_up * 3 + 1, trees_color[1] + 20)
        #                 image.put(right_up * 3 + 2, trees_color[2] + 20)
        #             except IndexError:
        #                 pass
        #
        #             try:
        #                 left = index - 1
        #                 image.put(left * 3 + 0, trees_color[0] + 10)
        #                 image.put(left * 3 + 1, trees_color[1] + 10)
        #                 image.put(left * 3 + 2, trees_color[2] + 10)
        #             except IndexError:
        #                 pass
        #
        #             try:
        #                 mid = index
        #                 image.put(mid * 3 + 0, trees_color[0])
        #                 image.put(mid * 3 + 1, trees_color[1])
        #                 image.put(mid * 3 + 2, trees_color[2])
        #             except IndexError:
        #                 pass
        #
        #             try:
        #                 right = index + 1
        #                 image.put(right * 3 + 0, trees_color[0] + 10)
        #                 image.put(right * 3 + 1, trees_color[1] + 10)
        #                 image.put(right * 3 + 2, trees_color[2] + 10)
        #             except IndexError:
        #                 pass
        #
        #             try:
        #                 bot_left = (row_num + 1) * self.resolution + col_num - 1
        #                 image.put(bot_left * 3 + 0, trees_color[0] + 20)
        #                 image.put(bot_left * 3 + 1, trees_color[1] + 20)
        #                 image.put(bot_left * 3 + 2, trees_color[2] + 20)
        #             except IndexError:
        #                 pass
        #
        #             try:
        #                 bot = (row_num + 1) * self.resolution + col_num
        #                 image.put(bot * 3 + 0, trees_color[0] + 10)
        #                 image.put(bot * 3 + 1, trees_color[1] + 10)
        #                 image.put(bot * 3 + 2, trees_color[2] + 10)
        #             except IndexError:
        #                 pass
        #
        #             try:
        #                 bot_right = (row_num + 1) * self.resolution + col_num + 1
        #                 image.put(bot_right * 3 + 0, trees_color[0] + 20)
        #                 image.put(bot_right * 3 + 1, trees_color[1] + 20)
        #                 image.put(bot_right * 3 + 2, trees_color[2] + 20)
        #             except IndexError:
        #                 pass
        #     # element location | rotation | scale | min | max
        #
        # print(f"instanced_objects took: {perf_counter() - start}")

        # start = perf_counter()
        #
        # if self.draw_progress:
        #     self.debug_view.render_image(image.tobytes())
        #
        # print(f"terrain tress took: {perf_counter() - start}")

        # TODO speed up took 6.3s

        start = perf_counter()

        image[self.point_data["id"][self.point_data["material"].str.contains(water_key)]] = water_color

        if self.draw_progress:
            self.debug_view.render_image(image.tobytes())

        print(f"terrain water took: {perf_counter() - start}")
        start = perf_counter()

        # Height Lines
        # NOTE speed up took: 109s
        if self.generate_height_lines:
            min_step = round(self.z_min / height_line_step_size) * height_line_step_size
            max_step = round(self.z_max / height_line_step_size) * height_line_step_size

            z_map_range = 32
            for step in range(((min_step * -1 if min_step < 0 else min_step) + max_step) // height_line_step_size, 0, -1):
                start_in = perf_counter()
                target_height = max_step - height_line_step_size * step
                lower_limit = target_height - height_line_step_size / 2
                upper_limit = target_height + height_line_step_size / 2
                points = dict(self.point_data[["id", "location_z"]]
                              [self.point_data_landscape & ((self.point_data.location_z > lower_limit) &
                               (self.point_data.location_z < upper_limit))].values)
                start_in_after = perf_counter()
                # NOTE 2-3x time spend below here -> optimize
                for point_id, point_z in points.items():
                    point_id = int(point_id)
                    point_z = float(point_z)
                    value_ = (point_z - target_height) / (height_line_step_size / 2)
                    value = int((value_ - 1) * -1 * z_map_range if value_ > 0 else (value_ + 1) * z_map_range)
                    value = value * (255 / z_map_range)
                    if value >= 200:  # TODO fix single points
                        neighbours = list(self.find_neighbours(point_id, points, self.resolution))
                        if 3 > self.num_equal(True,
                                              [abs(target_height - n) < abs(target_height - point_z) for n in neighbours]):
                            if 3 > self.num_equal(point_z, neighbours):
                                image[point_id] = height_line_color
                if self.draw_progress:
                    self.debug_view.render_image(image.tobytes())
                print(f"    getting: {start_in_after - start_in}, working: {perf_counter() - start_in_after}")
        print(f"height lines took: {perf_counter() - start}")

        # Streets
        # NOTE hit actor landscape, hit component = splinemeshcomponent
        start = perf_counter()

        # infrastructure_indexes = self.point_data[self.point_data_landscape]["hit_component"].str.startswith("splinemeshcomponent")

        infrastructure_indexes = self.point_data[self.point_data_landscape].loc[
            (self.point_data["hit_component"].str.startswith("splinemeshcomponent")),
        "id"
        ]

        spline_mesh_components = self.point_data[self.point_data["id"].isin(infrastructure_indexes)]["hit_component"].unique()
        number_components = len(spline_mesh_components)
        print(f"number_components: {number_components}")
        for component in spline_mesh_components:
            color = 0, 0, 0
            image[self.point_data.loc[self.point_data["hit_component"].str.match(component), "id"]] = color
        asphalt_indexes = self.point_data[infrastructure_indexes]["material"].str.contains("asphalt")

        # TODO group streets by name splinemeshcomponent_*number*

        # street_keys_query = "hit_actor LIKE" + " OR hit_actor LIKE".join([f"'%{key}%'"
        #                                                                   for key in street_keys]) \
        #                     + " OR hit_component LIKE" + " OR hit_component LIKE".join(
        #     [f"'%{key}%'"
        #      for key in street_keys]) + " OR material LIKE" + " OR material LIKE".join([f"'%{key}%'"
        #                                                                                 for key in street_keys])
        # query_string = f"SELECT id, hit_actor, hit_component, material " \
        #                f"FROM point " \
        #                f"WHERE " \
        #                f"{street_keys_query}"
        # result_street_query = self.database_cursor.execute(query_string)
        # print(f"streets query took: {perf_counter() - start}")
        # start = perf_counter()
        # # NOTE speed up takes 11s
        # for point in result_street_query:
        #     # TODO filter for other road types
        #     if any(key in point[2].lower() for key in bridge_keys):
        #         color = bridge_color
        #     elif any(key in point[2].lower() for key in main_road_keys):
        #         color = main_road_color
        #     elif any(key in point[2].lower() for key in road_keys):
        #         color = road_color
        #     elif any(key in point[3].lower() for key in small_road_keys):  # TODO find better keys for point[2]
        #         color = road_color
        #     else:
        #         if "roadblock" in point[2].lower():
        #             color = 0, 0, 255
        #         else:
        #             color = 255, 0, 0
        #     image.put(point[0] * 3 + 0, color[0])
        #     image.put(point[0] * 3 + 1, color[1])
        #     image.put(point[0] * 3 + 2, color[2])

        # image[infrastructure_indexes] = road_color

        if self.draw_progress:
            self.debug_view.render_image(image.tobytes())

        print(f"streets took: {perf_counter() - start}")

        # # Buildings
        #
        # start = perf_counter()
        # building_keys_query = "hit_component LIKE" + " OR hit_component LIKE".join(
        #     [f"'%{key}%'"
        #      for key in building_keys])
        # query_string = f"SELECT id " \
        #                f"FROM point " \
        #                f"WHERE " \
        #                f"{building_keys_query}"
        # result_buildings_query = self.database_cursor.execute(query_string)
        # print(f"buildings query took: {perf_counter() - start}")
        # start = perf_counter()
        # # NOTE speed up takes 23s
        # for point in result_buildings_query:
        #     image.put(point[0] * 3 + 0, building_color[0])
        #     image.put(point[0] * 3 + 1, building_color[1])
        #     image.put(point[0] * 3 + 2, building_color[2])
        #
        # if self.draw_progress:
        #     self.debug_view.render_image(image.tobytes())
        #
        # print(f"buildings took: {perf_counter() - start}")
        return image.reshape(self.resolution, self.resolution, 3, order="C")

    def generate_image(self):  # TODO mege with generate from db
        image = Image.fromarray(self.generate_from_db())
        return image


# noinspection SpellCheckingInspection
mapper = Mapper("Narva_AAS_v1",
                in_memory_bool=False,
                generate_bool=True,
                generate__height_lines_bool=False,
                debug_view_bool=False,
                draw_progress=False)

#                      parsing   generating
# time took:           237.84    160.96
# time took in memory: 229.24    152.45
