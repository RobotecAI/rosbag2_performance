import shutil
import pathlib, yaml, csv
import numpy as np

import rclpy
from rclpy.node import Node

class DefaultMapper(dict):
    def __missing__(self, key):
        return '{'+key+'}'

class VoyagerCase(Node):

    def __init__(self):
        super().__init__('voyager_case')
        self.logger = rclpy.logging.get_logger("VOY")

        self.declare_parameter("raport_dir", str(pathlib.Path.cwd()))
        self.raport_dir = pathlib.Path(self.get_parameter("raport_dir").get_parameter_value().string_value).expanduser()

        self.declare_parameter("output_dir", str(pathlib.Path.cwd().joinpath("voyager_case")))
        self.output_dir = pathlib.Path(self.get_parameter("output_dir").get_parameter_value().string_value).expanduser()
        self.output_dir.mkdir(exist_ok=True, parents=True)

        self.declare_parameter("raport_template_dir", str(pathlib.Path(__file__).parent.absolute().joinpath("..", "bundles", "voyager", "template.html")))
        raport_template_dir = pathlib.Path(self.get_parameter("raport_template_dir").get_parameter_value().string_value).expanduser()

        with open(pathlib.Path(raport_template_dir), 'r') as raport_template_file:
            self.raport_template = raport_template_file.read()

        self.declare_parameter("description", "")
        config_path = self.get_parameter("description").get_parameter_value().string_value
        if config_path == "":
            raise RuntimeError("You must specify a description file: \n --ros-args -p description:=[PATH]")

        # Manage config file
        self.config = None
        path = pathlib.Path(config_path)
        self.voyager_dir = path.parents[0]
        if path.is_file():
            with open(path) as config_file:
                self.config = yaml.load(config_file)
        else:
            raise RuntimeError("{} is not correct yaml config file.".format(path))
        
        self.generate_voyager_results()

    def generate_voyager_results(self):
        html_kwargs = {"su":""}
        table = []
        index = 0
        for record in self.config["layout"]:
            with open(str(self.voyager_dir.joinpath(record)), 'r') as description_file:
                data = yaml.load(description_file)
                benchmark_name = str(data["benchmark"]["id"])+"-"+str(data["benchmark"]["tag"])
                raport_file = pathlib.Path(self.raport_dir).expanduser().joinpath(benchmark_name).joinpath("raport.yaml")
                if raport_file.exists():
                    with open(str(raport_file), 'r') as data_file:
                        raport_data = yaml.load(data_file)
                        table.append("{:-6.2F}".format(raport_data["messages"]["percent"]))
                        images_dir = self.output_dir.joinpath("images")
                        images_dir.mkdir(exist_ok=True, parents=True)
                        shutil.copy(str(raport_file.parents[0].joinpath("plots.jpg")), str(images_dir.joinpath(benchmark_name+".jpg")))
                        html_kwargs["su"] += ("<img src='images/"+benchmark_name+".jpg'></img><br>\n")
                else:
                    table.append("  n/a")

        print("==================================")
        print("Voyager case results: \n")
        print("\t", ["     1", "    10", "   100", "  1000"])
        print("1KB \t", table[:4])
        print("10KB \t",table[4:8])
        print("100KB \t",table[8:12])
        print("1000KB \t",table[12:16])
        print()

        
        for row in range(0, 4):
            for col in range(0, 4):
                val = "n/a" if row*4+col >= len(table) else table[row*4+col]
                html_kwargs.update({"t{}{}".format(row,col):val})
        out_html = self.raport_template.format_map(DefaultMapper(**html_kwargs))

        with open(str(self.output_dir.joinpath("voyager_raport.html")), 'w') as outfile:
            outfile.write(out_html)

def main():
    rclpy.init()
    node = VoyagerCase()
    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.1)
        rclpy.shutdown()
    node.destroy_node()

if __name__ == '__main__':
    main()
