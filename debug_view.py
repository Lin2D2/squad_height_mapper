import asyncio

import pygame as pg


class DebugView:
    def __init__(self, image, resolution, database_cursor, compare_image):
        pg.init()
        pg.font.init()
        pg.display.set_caption('Height Mapper Debug View')

        self.image = image
        self.resolution = resolution
        self.database_cursor = database_cursor

        self.frames_per_second = 60
        self.scale = 2  # TODO fix scaling and add zoom
        self.window_width = 1920
        self.window_height = 1080
        self.display = pg.display.set_mode((self.window_width, self.window_height))

        self.clock = pg.time.Clock()

        self.marker_rect = pg.Rect((0, 0), (3, 3))

        self.debug_text_margin = 10
        self.debug_rect_size = (800, 400)
        self.debug_rect_pos = (
            self.window_width - self.debug_rect_size[0], self.window_height - self.debug_rect_size[1])
        self.debug_rect = pg.Rect(self.debug_rect_pos, self.debug_rect_size)

        debug_rect_elements = 8

        self.debug_rect_pixel_location = pg.Rect(self.debug_rect_pos,
                                                 (self.debug_rect_size[0],
                                                  self.debug_rect_size[1] / debug_rect_elements))
        self.debug_rect_data_location = pg.Rect(
            (self.debug_rect_pos[0], self.debug_rect_pos[1] + self.debug_rect_size[1] / debug_rect_elements),
            (self.debug_rect_size[0], self.debug_rect_size[1] / debug_rect_elements))
        self.debug_rect_data_actor = pg.Rect(
            (self.debug_rect_pos[0], self.debug_rect_pos[1] + self.debug_rect_size[1] * 2 / debug_rect_elements),
            (self.debug_rect_size[0], self.debug_rect_size[1] / debug_rect_elements * 2))
        self.debug_rect_data_component = pg.Rect(
            (self.debug_rect_pos[0], self.debug_rect_pos[1] + self.debug_rect_size[1] * 4 / debug_rect_elements),
            (self.debug_rect_size[0], self.debug_rect_size[1] / debug_rect_elements * 2))
        self.debug_rect_data_material = pg.Rect(
            (self.debug_rect_pos[0], self.debug_rect_pos[1] + self.debug_rect_size[1] * 6 / debug_rect_elements),
            (self.debug_rect_size[0], self.debug_rect_size[1] / debug_rect_elements * 2))

        self.font = pg.font.SysFont('Comic Sans MS', 15)

        self.image = pg.image.frombuffer(self.image, (self.resolution, self.resolution), "RGB").convert()
        self.compare_image = pg.image.load(compare_image).convert()

        self.image_x = 0
        self.image_y = 0

        self.display.blit(self.image, (self.image_x, self.image_y))

        pg.display.update()

        self.image_switch = False
        self.mouse_drag = False
        self.mouse_x_offset, self.mouse_y_offset = 0, 0

        self.query_result = None

    def render_image(self, image):
        image_scale = pg.transform.scale(pg.image.frombytes(image, (self.resolution, self.resolution), "RGB"),
                                         (self.window_width, self.window_height))
        self.display.blit(image_scale, (0, 0))
        pg.display.update()

    def run(self):
        while True:
            self.clock.tick(self.frames_per_second)

            mouse_x, mouse_y = pg.mouse.get_pos()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    # sys.exit()
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        query_string = f"SELECT location_x, location_y, location_z, hit_actor, hit_component, material " \
                                       f"FROM point WHERE id LIKE {self.resolution * (mouse_y - self.image_y) + (mouse_x - self.image_x)}"  # TODO wrong query or pos
                        self.query_result = self.database_cursor.execute(query_string).fetchall()
                        print(
                            f"x: {mouse_x - self.image_x}, y: {mouse_y - self.image_y}, xy: {self.resolution * (mouse_y - self.image_y) + (mouse_x - self.image_x)}")
                        print(f"{self.query_result}\n")
                    elif event.button == 3:
                        self.mouse_x_offset, self.mouse_y_offset = mouse_x, mouse_y
                        self.mouse_drag = True
                elif event.type == pg.MOUSEMOTION and self.mouse_drag:
                    current_image_x = self.image_x + mouse_x - self.mouse_x_offset
                    current_image_y = self.image_y + mouse_y - self.mouse_y_offset
                    self.mouse_x_offset, self.mouse_y_offset = mouse_x, mouse_y
                    if 0 > current_image_x > self.window_width - self.resolution:
                        self.image_x = current_image_x
                    if 0 > current_image_y > self.window_height - self.resolution:
                        self.image_y = current_image_y
                elif event.type == pg.MOUSEBUTTONUP and self.mouse_drag:
                    self.mouse_drag = False
                    self.mouse_x_offset, self.mouse_y_offset = 0, 0
                elif event.type == pg.KEYUP:
                    if event.key == pg.K_f:
                        self.image_switch = not self.image_switch

            self.display.blit(self.compare_image if self.image_switch else self.image, (self.image_x, self.image_y))
            pg.draw.rect(self.display, (255, 255, 255), self.debug_rect_pixel_location)
            pg.draw.rect(self.display, (0, 0, 0), pg.Rect(self.debug_rect_pixel_location.x + 5,
                                                          self.debug_rect_pixel_location.y + 5,
                                                          self.debug_rect_pixel_location.width - 5 * 2,
                                                          self.debug_rect_pixel_location.height - 5 * 2))
            pg.draw.rect(self.display, (255, 0, 255), self.debug_rect_data_location)
            pg.draw.rect(self.display, (0, 0, 0), pg.Rect(self.debug_rect_data_location.x + 5,
                                                          self.debug_rect_data_location.y + 5,
                                                          self.debug_rect_data_location.width - 5 * 2,
                                                          self.debug_rect_data_location.height - 5 * 2))
            pg.draw.rect(self.display, (0, 0, 255), self.debug_rect_data_actor)
            pg.draw.rect(self.display, (0, 0, 0), pg.Rect(self.debug_rect_data_actor.x + 5,
                                                          self.debug_rect_data_actor.y + 5,
                                                          self.debug_rect_data_actor.width - 5 * 2,
                                                          self.debug_rect_data_actor.height - 5 * 2))
            pg.draw.rect(self.display, (255, 255, 0), self.debug_rect_data_component)
            pg.draw.rect(self.display, (0, 0, 0), pg.Rect(self.debug_rect_data_component.x + 5,
                                                          self.debug_rect_data_component.y + 5,
                                                          self.debug_rect_data_component.width - 5 * 2,
                                                          self.debug_rect_data_component.height - 5 * 2))
            pg.draw.rect(self.display, (0, 255, 0), self.debug_rect_data_material)
            pg.draw.rect(self.display, (0, 0, 0), pg.Rect(self.debug_rect_data_material.x + 5,
                                                          self.debug_rect_data_material.y + 5,
                                                          self.debug_rect_data_material.width - 5 * 2,
                                                          self.debug_rect_data_material.height - 5 * 2))
            pixel_location_label = self.font.render("Pixel Location:", False, (255, 0, 0))
            pixel_location_text = self.font.render(
                f"X: {mouse_x - self.image_x}, Y: {mouse_y - self.image_y}",
                False, (255, 0, 0)
            )
            blits_list = [(pixel_location_label,
                           (self.debug_rect_pixel_location.x + self.debug_text_margin,
                            self.debug_rect_pixel_location.y + (
                                    self.debug_rect_pixel_location.height - self.debug_text_margin * 2) / 4 * 2
                            - pixel_location_text.get_height() / 2)),
                          (pixel_location_text,
                           (self.debug_rect_pixel_location.x + self.debug_text_margin,
                            self.debug_rect_pixel_location.y + (
                                    self.debug_rect_pixel_location.height - self.debug_text_margin * 2) / 4 * 2
                            + pixel_location_text.get_height() / 2)),
                          ]

            if self.query_result:
                data_location_label = self.font.render("Data Location:", False, (255, 0, 0))
                data_actor_label = self.font.render("Data Actor:", False, (255, 0, 0))
                data_component_label = self.font.render("Data Component:", False, (255, 0, 0))
                data_material_label = self.font.render("Data Material:", False, (255, 0, 0))
                data_location_text = None
                for point in self.query_result:
                    if "landscape" in point[3]:
                        data_location_text = self.font.render(
                            f"X: {point[0]}, Y: {point[1]}, Z: {point[2]}",
                            False, (255, 0, 0)
                        )
                if not data_location_text:
                    raise Exception("no landscape hit found")
                blits_list += [
                    (data_location_label,
                     (self.debug_rect_data_location.x + self.debug_text_margin,
                      self.debug_rect_data_location.y + (
                              self.debug_rect_data_location.height - self.debug_text_margin * 2) / 4 * 2
                      - data_location_text.get_height() / 2)),
                    (data_location_text,
                     (self.debug_rect_data_location.x + self.debug_text_margin,
                      self.debug_rect_data_location.y + (
                              self.debug_rect_data_location.height - self.debug_text_margin * 2) / 4 * 2
                      + data_location_text.get_height() / 2)),
                    (data_actor_label,
                     (self.debug_rect_data_actor.x + self.debug_text_margin,
                      self.debug_rect_data_actor.y + (
                              self.debug_rect_data_actor.height - self.debug_text_margin * 2) / 12 * 2
                      - data_location_text.get_height() / 2)),
                    (data_component_label,
                     (self.debug_rect_data_component.x + self.debug_text_margin,
                      self.debug_rect_data_component.y + (
                              self.debug_rect_data_component.height - self.debug_text_margin * 2) / 12 * 2
                      - data_location_text.get_height() / 2)),
                    (data_material_label,
                     (self.debug_rect_data_material.x + self.debug_text_margin,
                      self.debug_rect_data_material.y + (
                              self.debug_rect_data_material.height - self.debug_text_margin * 2) / 12 * 2
                      - data_location_text.get_height() / 2)),
                ]
                for index, point in enumerate(self.query_result):
                    data_actor_text = self.font.render(
                        f"{index + 1}: {point[3]}",
                        False, (255, 0, 0)
                    )
                    data_component_text = self.font.render(
                        f"{index + 1}: {point[4]}",
                        False, (255, 0, 0)
                    )
                    data_material_text = self.font.render(
                        f"{index + 1}: {point[5]}",
                        False, (255, 0, 0)
                    )
                    blits_list += [(data_actor_text,
                                    (self.debug_rect_data_actor.x + self.debug_text_margin,
                                     self.debug_rect_data_actor.y + self.debug_text_margin + (
                                             self.debug_rect_data_actor.height - self.debug_text_margin * 2) / 8
                                     + (data_actor_label.get_height() / 2 + self.debug_text_margin) * index)),
                                   (data_component_text,
                                    (self.debug_rect_data_component.x + self.debug_text_margin,
                                     self.debug_rect_data_component.y + self.debug_text_margin + (
                                             self.debug_rect_data_component.height - self.debug_text_margin * 2) / 8
                                     + (data_component_label.get_height() / 2 + self.debug_text_margin) * index)),
                                   (data_material_text,
                                    (self.debug_rect_data_material.x + self.debug_text_margin,
                                     self.debug_rect_data_material.y + self.debug_text_margin + (
                                             self.debug_rect_data_material.height - self.debug_text_margin * 2) / 8
                                     + (data_material_label.get_height() / 2 + self.debug_text_margin) * index)),
                                   ]
            self.display.blits(blits_list)

            self.marker_rect.update(mouse_x, mouse_y, 3, 3)
            pg.draw.rect(self.display, (255, 0, 0), self.marker_rect)

            pg.display.update()
