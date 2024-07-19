import json
import os.path
import statistics
import time

import unreal


# 1uu = 1cm would be 100.0


def get_dir_and_type(_object):
    print("-------------------------------------")
    print(type(_object))
    for e in dir(_object):
        print(e)
    print("-------------------------------------")


# class HitResult:
#     blocking_hit = False,
#     initial_overlap = False,
#     time = 0.0,
#     distance = 0.0,
#     location = [0.0, 0.0, 0.0],
#     impact_point = [0.0, 0.0, 0.0],
#     normal = [0.0, 0.0, 0.0],
#     impact_normal = [0.0, 0.0, 0.0],
#     phys_mat = None,
#     hit_actor = None,
#     hit_component = None,
#     hit_bone_name = 'None',
#     hit_item = 0,
#     element_index = 0,
#     face_index = 0,
#     trace_start = [0.0, 0.0, 0.0],
#     trace_end = [0.0, 0.0, 0.0]
#
#     def __init__(self, blocking_hit=None, initial_overlap=None, time=None, distance=None, location=None,
#                  impact_point=None, normal=None, impact_normal=None, phys_mat=None, hit_actor=None,
#                  hit_component=None, hit_bone_name=None, hit_item=None, element_index=None,
#                  face_index=None, trace_start=None, trace_end=None):
#         if blocking_hit is not None:
#             self.blocking_hit = blocking_hit
#         if initial_overlap is not None:
#             self.initial_overlap = initial_overlap
#         if time is not None:
#             self.time = time
#         if distance is not None:
#             self.distance = distance
#         if location is not None:
#             self.location = location.to_tuple()
#         if impact_point is not None:
#             self.impact_point = impact_point.to_tuple()
#         if normal is not None:
#             self.normal = normal.to_tuple()
#         if impact_normal is not None:
#             self.impact_normal = impact_normal.to_tuple()
#         if phys_mat is not None:
#             self.phys_mat = phys_mat
#         if hit_actor is not None:
#             self.hit_actor = hit_actor
#         if hit_component is not None:
#             self.hit_component = hit_component
#         if hit_bone_name is not None:
#             self.hit_bone_name = hit_bone_name
#         if hit_item is not None:
#             self.hit_item = hit_item
#         if element_index is not None:
#             self.element_index = element_index
#         if face_index is not None:
#             self.face_index = face_index
#         if trace_start is not None:
#             self.trace_start = trace_start.to_tuple()
#         if trace_end is not None:
#             self.trace_end = trace_end.to_tuple()
#
#     @classmethod
#     def from_tuple(cls, in_tuple):
#         assert len(in_tuple) == 17
#         return cls(in_tuple[0], in_tuple[1], in_tuple[2], in_tuple[3], in_tuple[4], in_tuple[5],
#                    in_tuple[6], in_tuple[7], in_tuple[8], in_tuple[9], in_tuple[10], in_tuple[11],
#                    in_tuple[12], in_tuple[13], in_tuple[14], in_tuple[15], in_tuple[16])


class Transform:
    location = [0.0, 0.0, 0.0]
    rotation = [0.0, 0.0, 0.0]
    scale = [0.0, 0.0, 0.0]

    def __init__(self, location=None, rotation=None, scale=None):
        if location is not None:
            self.location = location.to_tuple()
        if rotation is not None:
            self.rotation = rotation.to_tuple()
        if scale is not None:
            self.scale = scale.to_tuple()

    @classmethod
    def from_tuple(cls, in_tuple):
        assert len(in_tuple) == 3
        return cls(in_tuple[0], in_tuple[1], in_tuple[2])

    def to_dict(self):
        return {
            "location": self.location,
            "rotation": self.rotation,
            "scale": self.scale,
        }


class Bounds:
    max_x = None
    max_y = None
    max_z = None
    min_x = None
    min_y = None
    min_z = None

    def __init__(self, max_x=None, max_y=None, max_z=None, min_x=None, min_y=None, min_z=None):
        if max_x is not None:
            self.max_x = max_x
        if max_y is not None:
            self.max_y = max_y
        if max_z is not None:
            self.max_z = max_z
        if min_x is not None:
            self.min_x = min_x
        if min_y is not None:
            self.min_y = min_y
        if min_z is not None:
            self.min_z = min_z

    @classmethod
    def from_tuple(cls, in_tuple):
        assert len(in_tuple) == 2
        return cls(in_tuple[1][0], in_tuple[1][1], in_tuple[1][2], in_tuple[0][0], in_tuple[0][1], in_tuple[0][2])

    def __str__(self):
        return (f"max_x: {self.max_x}, min_x: {self.min_x}, max_y: {self.max_y}, "
                f"min_y: {self.min_y}, max_z: {self.max_z}, min_z: {self.min_z}")

    def set_by_index(self, _index, _max, _min):
        if _index == 0:
            self.max_x = _max
            self.min_x = _min
        elif _index == 1:
            self.max_y = _max
            self.min_y = _min
        elif _index == 2:
            self.max_z = _max
            self.min_z = _min
        else:
            raise IndexError

    def to_dict(self):
        return {"max_x": self.max_x, "min_x": self.min_x, "max_y": self.max_y,
                "min_y": self.min_y, "max_z": self.max_z, "min_z": self.min_z}

    def max(self):
        return tuple((self.max_x, self.max_y, self.max_z))

    def min(self):
        return tuple((self.min_x, self.min_y, self.min_z))

    def get_x_extend(self):
        return abs(self.max_x) + abs(self.min_x)

    def get_y_extend(self):
        return abs(self.max_y) + abs(self.min_y)

    def get_z_extend(self):
        return abs(self.max_z) + abs(self.min_z)


class ExtractLevelData:
    def __init__(self, map_to_load, step_size, debug=False):
        self.step_size = step_size
        self.debug = debug
        self.current_map = unreal.EditorLevelLibrary.get_editor_world()

        print(f"current map: {self.current_map.get_name()}")

        if self.current_map.get_full_name().find(map_to_load.split("/")[-1]) == -1:
            loaded = unreal.EditorLevelLibrary.load_level(map_to_load)

            if not loaded:
                raise Exception(f"Failed to load {map_to_load}")

            self.current_map = unreal.EditorLevelLibrary.get_editor_world()

            print(f"loaded {map_to_load}")

        self.object_data = {
            "map_name": self.current_map.get_name(),
            "step_size": step_size,
            "poi_marker": [],
            "map_bounds": {"max_x": None, "min_x": None, "max_y": None,
                           "min_y": None, "max_z": None, "min_z": None}
        }

        self.export_folder_path = f"C:/Users/space/Desktop/squad_height_mapper/{self.current_map.get_name()}"

        self.level_actors = unreal.EditorLevelLibrary.get_all_level_actors()
        # Landscape
        self.landscape = list(filter(lambda x: type(x) is unreal.Landscape, self.level_actors))[0]
        # LandscapeSplinesComponent
        self.landscape_splines_component = self.landscape.get_components_by_class(unreal.LandscapeSplinesComponent)[0]
        # StaticMeshActor
        self.static_mesh_actor = list(filter(lambda x: type(x) is unreal.StaticMeshActor, self.level_actors))
        # SQInstancedStaticMeshActor
        self.instanced_static_mesh_actor = list(filter(lambda x: type(x) is unreal.SQInstancedStaticMeshActor, self.level_actors))
        # Actor
        self.actor = list(filter(lambda x: type(x) is unreal.Actor, self.level_actors))
        # PrefabActor
        self.prefab_actor = list(filter(lambda x: type(x) is unreal.PrefabActor, self.level_actors))
        # SQMapBoundary
        self.sq_map_boundary = list(filter(lambda x: type(x) is unreal.SQMapBoundary, self.level_actors))[0]
        # LevelBounds
        level_bounds = list(filter(lambda x: type(x) is unreal.LevelBounds, self.level_actors))
        # SQProtectionZone
        # SQLake
        # SQDeployable

        # NOTE POI Marker
        poi_markers = list(filter(lambda x: type(x) is unreal.TextRenderActor and x.get_folder_path() == "POI Markers",
                                  self.level_actors))
        markers = []
        for e in poi_markers:
            marker_location = e.get_actor_location().to_tuple()
            markers.append({"name": e.get_name(),
                            "location_x": marker_location[0],
                            "location_y": marker_location[1],
                            "location_z": marker_location[2]})
        self.object_data["poi_marker"] = markers

        # NOTE Level Bounds
        self.level_bound = Bounds()
        transform = Transform.from_tuple(level_bounds[-1].get_actor_transform().to_tuple())
        # z limits
        half_scale = transform.scale[2] * 0.5
        bounds_max = half_scale + transform.location[2]
        bounds_min = half_scale * -1 + transform.location[2]
        self.level_bound.set_by_index(2, bounds_max, bounds_min)

        x_bound = []
        y_bound = []
        num_points = self.sq_map_boundary.xy_boundary.get_number_of_spline_points()
        for i in range(num_points):
            point = self.sq_map_boundary.xy_boundary.get_location_at_spline_point(
                i,
                unreal.SplineCoordinateSpace.WORLD
            ).to_tuple()
            x_bound.append(point[0])
            y_bound.append(point[1])
        self.level_bound.set_by_index(0, max(x_bound), min(x_bound))
        self.level_bound.set_by_index(1, max(y_bound), min(y_bound))

        self.object_data["map_bounds"] = self.level_bound.to_dict()

        # NOTE write map_data to file
        with open(os.path.join(self.export_folder_path, "map_data.json"), "w+") as file:
            json.dump(self.object_data, file)

    def run(self):
        self.get_instances()
        self.run_mapper()

    def get_instances(self):
        data = {
            "landscape_spline_mesh_components": dict()
        }
        # LandscapeSplinesMeshComponents
        landscape_spline_mesh_components = self.landscape_splines_component.get_spline_mesh_components()

        for spline_mesh_component in landscape_spline_mesh_components:
            data["landscape_spline_mesh_components"].update({
                    spline_mesh_component.get_full_name().lower():
                    {
                        "materials": [material.get_full_name().lower() for material in spline_mesh_component.get_materials()],
                        "world_transform": Transform.from_tuple(spline_mesh_component.get_world_transform().to_tuple()).to_dict(),
                        "static_mesh_path_name": spline_mesh_component.static_mesh.get_path_name().lower(),
                        "static_mesh_bounding_box": Bounds.from_tuple([e.to_tuple() for e in spline_mesh_component.static_mesh.get_bounding_box().to_tuple()]).to_dict()
                    }
                }
            )

        with open(os.path.join(
                self.export_folder_path,
                f"{self.current_map.get_name()}_{self.step_size}_get_instances.json"),
                "w+") as file:
            json.dump(data, file)
            # json.dump(data, file, indent=2)

    def run_mapper(self):
        map_to_load = self.current_map
        self.current_map = unreal.EditorLevelLibrary.get_editor_world()

        print(f"current map: {self.current_map.get_name()}")

        if self.current_map.get_full_name().find(map_to_load.get_name()) == -1:
            loaded = unreal.EditorLevelLibrary.load_level(map_to_load.get_full_name())

            if not loaded:
                raise Exception(f"Failed to load {map_to_load}")

            self.current_map = unreal.EditorLevelLibrary.get_editor_world()

            print(f"loaded {map_to_load}")

        print(f"bounds: {self.level_bound}")

        addon_margin = 1000

        if self.level_bound.max_x > 0:
            max_x = self.level_bound.max_x + addon_margin
        else:
            max_x = self.level_bound.max_x - addon_margin
        if self.level_bound.min_x < 0:
            min_x = self.level_bound.min_x - addon_margin
        else:
            min_x = self.level_bound.min_x + addon_margin
        if self.level_bound.max_y > 0:
            max_y = self.level_bound.max_y + addon_margin
        else:
            max_y = self.level_bound.max_y - addon_margin
        if self.level_bound.min_y < 0:
            min_y = self.level_bound.min_y - addon_margin
        else:
            min_y = self.level_bound.min_y + addon_margin
        sum_x = abs(max_x) + abs(min_x)
        sum_y = abs(max_y) + abs(min_y)
        diff_half = abs(sum_x - sum_y) / 2
        if sum_x > sum_y:
            if max_y > 0:
                max_y = max_y + diff_half
            else:
                max_y = max_y - diff_half
            if min_y < 0:
                min_y = min_y - diff_half
            else:
                min_y = min_y + diff_half
        else:
            if max_x > 0:
                max_x = max_x + diff_half
            else:
                max_x = max_x - diff_half
            if min_x < 0:
                min_x = min_x - diff_half
            else:
                min_x = min_x + diff_half

        x_steps = int((abs(int(min_x - 0.5)) + abs(int(max_x + 0.5))) / self.step_size) + 1
        y_steps = int((abs(int(min_y - 0.5)) + abs(int(max_y + 0.5))) / self.step_size) + 1

        if self.debug:
            print(f"x_steps: {x_steps}")
            print(f"y_steps: {y_steps}")
            print(f"len x_steps: {len(list(range(int(min_x - 0.5), int(max_x + 0.5), self.step_size)))}")
            print(f"len y_steps: {len(list(range(int(min_y - 0.5), int(max_y + 0.5), self.step_size)))}")

        half_step_size = int(self.step_size / 2)

        if not os.path.exists(self.export_folder_path):
            os.mkdir(self.export_folder_path)

        with open(os.path.join(
                self.export_folder_path,
                f"{self.current_map.get_name()}_{self.step_size}_mapperoutput.csv"),
                "w+") as csv:
            csv.write("id,"
                      "location_x,location_y,location_z,"
                      # "impact_normal_x,impact_normal_y,impact_normal_z,"
                      "hit_actor,hit_actor_path,"
                      "hit_component,"
                      "material\n")

        with open(os.path.join(
                self.export_folder_path,
                f"{self.current_map.get_name()}_{self.step_size}_mapperoutput.csv"),
                "ab") as csv:
            hit_stack = []
            # start_t_h = []
            for y_i, y in enumerate(range(int(min_y - 0.5), int(max_y + 0.5), self.step_size)):
                for x_i, x in enumerate(range(int(min_x - 0.5), int(max_x + 0.5), self.step_size)):
                    start = unreal.Vector(x + half_step_size, y + half_step_size, self.level_bound.max_z)
                    end = unreal.Vector(x + half_step_size, y + half_step_size, self.level_bound.min_z)

                    if self.debug:
                        x = -55990.0
                        y = 41020.0
                        start = unreal.Vector(x, y, self.level_bound.max_z)
                        end = unreal.Vector(x, y, self.level_bound.min_z)

                    ignore_actors = unreal.Array(unreal.Actor)
                    objects = unreal.Array.cast(
                        unreal.ObjectTypeQuery,
                        [
                            unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1,
                            unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2,
                            unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY3,
                            unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY4,
                            unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY5,
                            unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY6,
                            unreal.ObjectTypeQuery.ECC_DEPLOYABLE,
                            unreal.ObjectTypeQuery.ECC_WATER,
                        ]
                    )

                    # NOTE list of ObjectTypeQuery and assumptions of type
                    # unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1          # WorldStatic
                    # unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2          # WorldDynamic
                    # unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY3          # Pawn
                    # unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY4          # PhysicsBody
                    # unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY5          # Vehicle
                    # unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY6          # Destructible
                    # unreal.ObjectTypeQuery.ECC_PROJECTILE              # Projectile
                    # unreal.ObjectTypeQuery.ECC_DETECT_ZONE             # DetectZone
                    # unreal.ObjectTypeQuery.ECC_DEPLOYABLE              # Deployable
                    # unreal.ObjectTypeQuery.ECC_INTERACT                # Interact
                    # unreal.ObjectTypeQuery.ECC_FOB_CONSTRUCTION_VOLUME # FOBConstructionVolume
                    # unreal.ObjectTypeQuery.ECC_THROWABLE               # Throwable
                    # unreal.ObjectTypeQuery.ECC_WATER                   # Water
                    # unreal.ObjectTypeQuery.ECC_INFRARED                # Infrared
                    # not here Visibility and Camera

                    # Line Trace

                    # NOTE 30% time speed here
                    hits = unreal.SystemLibrary.line_trace_multi_for_objects(
                        self.current_map,
                        start,
                        end,
                        objects,
                        True,
                        ignore_actors,
                        unreal.DrawDebugTrace.NONE,
                        True
                    )

                    # start_t_h_c = time.perf_counter()
                    # NOTE 60% time speed here 0.03082
                    for hit in hits:
                        # NOTE 30%
                        hit = hit.to_tuple()
                        hit_location = hit[4].to_tuple()
                        # hit_normal = hit[6].to_tuple()
                        hit_actor = f"{hit[9].get_actor_label()}".lower()
                        hit_actor_path = f"{hit[9].get_folder_path()}".lower()
                        if "landscape/surround" == hit_actor_path:  # skipping surround landscape mesh
                            continue
                        # NOTE 30%
                        hit_stack.append(f"{y_i * x_steps + x_i},"
                                         f"{int(hit_location[0])},"
                                         f"{int(hit_location[1])},"
                                         f"{int(hit_location[2])},"
                                         # f"{hit_normal[0]},"
                                         # f"{hit_normal[1]},"
                                         # f"{hit_normal[2]},"
                                         f"{hit_actor},"
                                         f"{hit_actor_path},"
                                         f"{hit[10].get_full_name().lower()},"
                                         f"{hit[8].get_full_name().lower()}\n")
                        # NOTE: exit loop when landscape is hit so ocean is skipped when below landscape
                        #       !!! landscape always is last hit !!!
                        if "landscape" == hit_actor_path:
                            break
                    # start_t_h.append(time.perf_counter() - start_t_h_c)

                    if self.debug:
                        for hit in hit_stack:
                            for e in hit.split(","):
                                print(e)
                            print("--------------------------------------------")
                        break

                    # start_t_w = time.perf_counter()
                    csv.write(bytes("".join(hit_stack), encoding='utf-8'))
                    # print(f"write took: {(time.perf_counter() - start_t_w)}s")
                    hit_stack.clear()

                if self.debug:
                    break

                # print(f"median data extract took: {(statistics.median(start_t_h))}s")
                # print(f"sum of data extracts took: {(sum(start_t_h))}s")

                # if y_i % 10 == 0:
                # # start_t_w = time.perf_counter()
                # csv.write(bytes("".join(hit_stack), encoding='utf-8'))
                # # print(f"write took: {(time.perf_counter() - start_t_w)}s")
                # hit_stack.clear()
                # if True:  # FIXME remove
                #     break
        del hit_stack


if __name__ == "__main__":
    map_to_load_ = "/Game/Maps/Narva/Gameplay_Layers/Narva_AAS_v1"
    # map_to_load_ = "/Game/Maps/Yehorivka/Gameplay_Layers/Yehorivka_AAS_v1"

    print("start")

    extract_level_data = ExtractLevelData(map_to_load_, 100, debug=False)

    start_t = time.perf_counter()
    extract_level_data.get_instances()
    print(f"get_instances took: {(time.perf_counter() - start_t)}s")

    # start_t = time.perf_counter()
    # extract_level_data.run_mapper()
    # print(f"mapper took: {(time.perf_counter() - start_t)}s")

    print("end")

# # root_component = landscape.root_component
# # absolute_location = root_component.get_world_location().to_tuple()
# # absolute_rotation = root_component.get_world_rotation().to_tuple()
# # print(f"location: {absolute_location}, rotation: {absolute_rotation}")
#
# landscape_splines_component = landscape.get_components_by_class(unreal.LandscapeSplinesComponent)[0]
#
# relative_location = landscape_splines_component.relative_location.to_tuple()
# relative_rotation = landscape_splines_component.relative_rotation.to_tuple()
# print(f"location: {relative_location}, rotation: {relative_rotation}")
#
# landscape_spline_mesh_components = landscape_splines_component.get_spline_mesh_components()
#
# spline_mesh_component = landscape_spline_mesh_components[5]
#
# # start_offset = landscape_spline_mesh_component.get_start_offset().to_tuple()
# # end_offset = landscape_spline_mesh_component.get_end_offset().to_tuple()
# # print(end_offset)
# start_pos = spline_mesh_component.get_start_position().to_tuple()
# end_pos = spline_mesh_component.get_end_position().to_tuple()
# rotation = spline_mesh_component.get_world_rotation().to_tuple()
# # bounds = tuple([bound.to_tuple() for bound in spline_mesh_component.get_local_bounds()])
# # spline_params = spline_mesh_component.spline_params
# # spline_params_start_pos = spline_params.start_pos.to_tuple()
# # spline_params_end_pos = spline_params.end_pos.to_tuple()
#
# print(f"{spline_mesh_component.static_mesh.get_name()}"
#       f"\nstart_pos: {start_pos}"
#       f"\nend_pos: {end_pos}"
#       f"\nrotation: {rotation}"
#       # f"\nbounds: {bounds}"
#       # f"\nstart_pos: {spline_params_start_pos}"
#       # f"\nend_pos: {spline_params_end_pos}"
#       )


