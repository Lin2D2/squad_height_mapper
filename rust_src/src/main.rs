use std::io;
use std::fs;
use std::collections::HashMap;

use polars::lazy::dsl::col;
use polars::prelude::*;
use image;

const MAP_DATA_PATH: &str = "/home/space/Documents/squad_height_mapper";  // TODO do this realative instead of absolute

const HEIGHT_LINE_STEP_SIZE: u32 = 1000;  // 2500 = 25m
// TODO write height in the line example: ----- 2000 ------

const DEFAULT_COLOR: [u8; 3] = [255, 253, 238];

const HEIGHT_LINE_COLOR: [u8; 3] = [128, 128, 128];

const GRASS_COLOR: [u8; 3] = [209, 240, 197];
const DIRT_COLOR: [u8; 3] = DEFAULT_COLOR;
const TREES_COLOR: [u8; 3] = [181, 194, 112];
const WATER_COLOR: [u8; 3] = [210, 232, 250];
const MUD_COLOR: [u8; 3] = [202, 203, 134];
const BRIDGE_COLOR: [u8; 3] = [255, 255, 0];  // TODO find bridge color
const MAIN_ROAD_COLOR: [u8; 3] = [255, 109, 44];
const ROAD_COLOR: [u8; 3] = [255, 166, 39];
const SIDE_ROAD_COLOR: [u8; 3] = [255, 255, 255];
const SMALL_ROAD_COLOR: [u8; 3] = [230, 160, 120];
const TRAIN_TRACK_COLOR: [u8; 3] = [102, 102, 102];
const BUILDING_COLOR: [u8; 3] = [168, 168, 168];


fn load_map_data(map_name: &str) -> PolarsResult<DataFrame> {
    let paths: fs::ReadDir = fs::read_dir(vec![MAP_DATA_PATH.to_owned(), map_name.to_string()].join("/")).unwrap();

    let mut _avalible_files: HashMap<u8, String> = HashMap::new();

    let mut _i:u8 = 1;
    for raw_path in paths {
        let path: fs::DirEntry = raw_path.unwrap();
        let file_path: String = path.path().display().to_string();
        let filename: String = path.file_name().into_string().unwrap();
        if filename.contains(".csv") {
            _avalible_files.insert(_i, file_path);
            println!("{}: {}", _i.to_string(), filename);
            _i += 1;
        }
    }

    // println!("select file to open by number: ");

    // let mut line: String = String::new();
    // io::stdin().read_line(&mut line).unwrap();

    // let input_as_u8: u8 = line.trim().parse::<u8>().expect("Input not an integer");
    // TODO remove DEBUG only
    let input_as_u8: u8 = 1;

    let csv_file_path: &String = &_avalible_files[&input_as_u8];

    println!("opening csv at: {}", csv_file_path);

    // TODO make this read folder and auto get file name or do it with input
    // let csv_file_name: &str = "Narva_AAS_v1_100_mapperoutput.csv";

    // let csv_file_path: String = vec![MAP_DATA_PATH.to_owned(), map_name.to_string(), csv_file_name.to_string()].join("/");

    CsvReadOptions::default()
    .with_has_header(true)
    .try_into_reader_with_file_path(Some(csv_file_path.into()))?
    .finish()
}


fn id_max_map_data(map_data: &DataFrame) -> f64 {
    map_data.column("id").unwrap().max::<f64>().unwrap().unwrap()
}


fn main() {
    println!("start");
    let map_name: &str = "Narva_AAS_v1";

    // Import data
    let map_data: DataFrame = load_map_data(map_name).expect("failed to load csv");
    // println!("{}", map_data.head(Some(10)));

    // Calc basic values
    let resolution: u32 = (id_max_map_data(&map_data) + 1.0).sqrt() as u32;
    println!("resolution: {}", resolution);

    let mut _image_buffer: Vec<Vec<u8>> = vec![[255, 253, 238].to_vec(); resolution.pow(2).try_into().unwrap()];

    // Do stuff

    // let map_data_landscape: DataFrame = map_data.filter(&map_data
    //     .column("hit_actor_path").unwrap()
    //     .equal("landscape").unwrap()).unwrap();
    let map_data_landscape: DataFrame = map_data.clone().lazy().filter(col("hit_actor_path").eq(lit("landscape"))).collect().unwrap();
    
    { // Grass
        let map_data_grass_locations: DataFrame = map_data_landscape.clone().lazy()
        .filter(col("material").str().contains(lit("grass"), false)).collect().unwrap();
        let grass_indexes: &Series = map_data_grass_locations.column("id").unwrap();
        println!("map_data_grass_locations length: {}", grass_indexes.head(Some(10)));

        for id in grass_indexes.i64().unwrap() {
            _image_buffer[id.unwrap() as usize] = GRASS_COLOR.to_vec();
        }
    }

    { // Water  // TODO dosent find anything
        let map_data_water_locations: DataFrame = map_data.clone().lazy()
        .filter(col("material").str().contains(lit("water"), false)).collect().unwrap();
        let grass_indexes: &Series = map_data_water_locations.column("id").unwrap();
        println!("map_data_water_locations length: {}", grass_indexes.head(Some(10)));

        for id in grass_indexes.i64().unwrap() {
            _image_buffer[id.unwrap() as usize] = WATER_COLOR.to_vec();
        }
    }

    { // for Heightlines
        let map_data_landscape_id_z: DataFrame= map_data_landscape.clone().select(["id", "location_z"]).unwrap();
        println!("map_data_landscape_id_z length: {}", map_data_landscape_id_z.head(Some(10)));
    }

    // Export final image
    let _image_buffer_flattend: Vec<u8> = _image_buffer.into_iter().flatten().collect::<Vec<u8>>();
    image::save_buffer_with_format(
        vec![MAP_DATA_PATH.to_owned(), map_name.to_string(), "tmp.png".to_string()].join("/"),
        &_image_buffer_flattend, 
        resolution, 
        resolution, 
        image::ColorType::Rgb8, 
        image::ImageFormat::Png).expect("failed to save image");

    println!("end");
}
