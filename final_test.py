import json
import math
import networkx as nx
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class RouteApp:
    def __init__(self, root):
        self.graph = nx.Graph()
        self.root = root
        self.root.title("Geolocation and 3D mapping")

        self.points = self.load_json("received_data.json")
        self.node_names = {}

        self.create_interface()

    def load_json(self, filename):
        try:
            with open(filename, "r") as file:
                data = json.load(file)

            self.graph.clear()  # Clear the graph before reloading data
            self.node_names = {}  # Clear node_names before reloading data

            for i, point in enumerate(data):
                if all(key in point for key in ["latitude", "longitude", "altitude"]):
                    self.graph.add_node(i, latitude=float(point["latitude"]), longitude=float(point["longitude"]), altitude=float(point["altitude"]))
                    self.node_names[i] = f"Node {i + 1}"
                    point.setdefault("name", f"Node {i + 1}")

            return data
        except FileNotFoundError:
            return []

    def save_json(self, filename):
        with open(filename, "w") as file:
            json.dump(self.points, file, indent=2)

    def update_node_name(self):
        selected_index = self.tree.selection()
        if selected_index:
            selected_index = int(selected_index[0][1:])
            new_name = self.name_entry.get()
            if new_name:
                self.node_names[selected_index] = new_name
                self.points[selected_index]["name"] = new_name
                self.save_json("received_data.json")
                self.update_tree()
            else:
                self.status_label.config(text="Please enter a name.")

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371000  # Radius of the Earth in meters
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return distance

    def add_path(self):
        selected_indices = self.tree.selection()
        if len(selected_indices) != 2:
            self.status_label.config(text="Select exactly two nodes to add a path.")
            return

        node1_index = int(selected_indices[0][1:])
        node2_index = int(selected_indices[1][1:])

        node1 = self.graph.nodes[node1_index]
        node2 = self.graph.nodes[node2_index]

        geo_distance = self.haversine_distance(node1['latitude'], node1['longitude'], node2['latitude'], node2['longitude'])
        altitude_difference = abs(node1['altitude'] - node2['altitude'])
        vertical_distance = math.sqrt(geo_distance**2 + altitude_difference**2)

        self.graph.add_edge(node1_index, node2_index, weight=vertical_distance)

        self.update_tree()
        self.status_label.config(text=f"Path added between {self.points[node1_index]['name']} and {self.points[node2_index]['name']}. "
                                    f"Distance: {geo_distance:.2f} meters. 3D Height: {altitude_difference:.2f} meters.")

    def find_shortest_path_astar(self, graph, start, goal):
        def heuristic(node1, node2):
            x1, y1, z1 = graph.nodes[node1]['latitude'], graph.nodes[node1]['longitude'], graph.nodes[node1]['altitude']
            x2, y2, z2 = graph.nodes[node2]['latitude'], graph.nodes[node2]['longitude'], graph.nodes[node2]['altitude']
            return math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

        path = nx.astar_path(graph, source=start, target=goal, heuristic=heuristic, weight='weight')
        return path

    def find_shortest_path(self):
        selected_indices = self.tree.selection()
        if len(selected_indices) != 2:
            self.status_label.config(text="Select exactly two nodes to find the shortest path.")
            return

        node1_index = int(selected_indices[0][1:])
        node2_index = int(selected_indices[1][1:])

        try:
            shortest_path_indices = self.find_shortest_path_astar(self.graph, node1_index, node2_index)
            total_distance = nx.shortest_path_length(self.graph, source=node1_index, target=node2_index, weight='weight')

            path_string = " --> ".join(self.points[i]["name"] for i in shortest_path_indices)

            self.status_label.config(text=f"Shortest path between {self.points[node1_index]['name']} and {self.points[node2_index]['name']}: {path_string}. "
                              f"Total Distance: {total_distance:.2f} meters.")
        except nx.NetworkXNoPath:
            self.status_label.config(text=f"No path found between Node {node1_index + 1} and Node {node2_index + 1}.")

    def delete_node(self):
        selected_index = self.tree.selection()
        if selected_index:
            selected_index = int(selected_index[0][1:])
            self.status_label.config(text=f"{self.points[selected_index]['name']} deleted.")
            
            del self.points[selected_index]
            self.save_json("received_data.json")
            self.update_tree()

    def create_3d_visualization(self):
     fig = plt.figure()
     ax = fig.add_subplot(111, projection='3d')

     for edge in self.graph.edges(data=True):
        node1 = edge[0]
        node2 = edge[1]
        weight = edge[2]['weight']

        # Extract coordinates
        x = [self.graph.nodes[node1]['latitude'], self.graph.nodes[node2]['latitude']]
        y = [self.graph.nodes[node1]['longitude'], self.graph.nodes[node2]['longitude']]
        z = [self.graph.nodes[node1]['altitude'], self.graph.nodes[node2]['altitude']]

        ax.plot(x, y, z, label=f'Weight: {weight:.2f}')

     for node_id, node in self.graph.nodes(data=True):
        x = node['latitude']
        y = node['longitude']
        z = node['altitude']

        # Scatter plot for nodes with creative icons
        node_name = self.get_node_name_from_json(node_id) if node_id not in self.node_names else self.node_names[node_id]

        ax.scatter(x, y, z, s=100, marker='*')

        # Annotate node with its name from the JSON data
        ax.text(x, y, z, node_name, fontsize=8, ha='left', va='bottom')

     ax.set_xlabel('Latitude')
     ax.set_ylabel('Longitude')
     ax.set_zlabel('Altitude')
     ax.set_title('3D Visualization of Nodes and Edges')

     plt.show()        

    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, point in enumerate(self.points):
            values = (point.get("latitude", ""), point.get("longitude", ""), point.get("altitude", ""), point.get("timestamp", ""))
            node_name = point.get("name", f"Node {i + 1}")  # Use the "name" attribute if available, else use default
            self.tree.insert("", "end", iid=f"I{i}", text=node_name, values=values)

    def get_node_name_from_json(self, node_index):
        try:
            with open("received_data.json", "r") as file:
                data = json.load(file)

            if 0 <= node_index < len(data):
                return data[node_index].get("name", f"Node {node_index + 1}")

        except FileNotFoundError:
            pass

        return f"Node {node_index + 1}"  # Default name if node not found or file not available

    def create_interface(self):
        self.tree = ttk.Treeview(self.root)
        self.tree["columns"] = ("Latitude", "Longitude", "Altitude", "Timestamp")

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)

        for i, point in enumerate(self.points):
            values = (point.get("latitude", ""), point.get("longitude", ""), point.get("altitude", ""), point.get("timestamp", ""))
            node_name = point.get("name", f"Node {i + 1}")  # Use the "name" attribute if available, else use default
            self.tree.insert("", "end", iid=f"I{i}", text=node_name, values=values)

        self.name_entry_label = ttk.Label(self.root, text="Enter new name:")
        self.name_entry = ttk.Entry(self.root)
        self.update_button = ttk.Button(self.root, text="Update Name", command=self.update_node_name)
        self.add_path_button = ttk.Button(self.root, text="Add Path", command=self.add_path)
        self.find_shortest_path_button = ttk.Button(self.root, text="Find Shortest Path", command=self.find_shortest_path)
        self.delete_node_button = ttk.Button(self.root, text="Delete Node", command=self.delete_node)
        self.visualization_button = ttk.Button(self.root, text="3D Visualization", command=self.create_3d_visualization)
        self.status_label = ttk.Label(self.root, text="")

        self.tree.pack(pady=5)
        self.name_entry_label.pack(pady=5)
        self.name_entry.pack(pady=5)
        self.update_button.pack(pady=5)
        self.add_path_button.pack(pady=5)
        self.find_shortest_path_button.pack(pady=5)
        self.delete_node_button.pack(pady=5)
        self.visualization_button.pack(pady=5)
        self.status_label.pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = RouteApp(root)
    root.mainloop()
