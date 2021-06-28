# standard imports
import os
# Setup paths for module imports
from .conftest import local_path, scratch_path, BasisTest, pyaedt_unittest_check_desktop_error

# Import required modules
from pyaedt import Hfss
from pyaedt.generic.filesystem import Scratch
from pyaedt.modeler.Primitives import Polyline, PolylineSegment
from pyaedt.modeler.Object3d import Object3d
from pyaedt.modeler.GeometryOperators import GeometryOperators
from pyaedt.application.Analysis import CoordinateSystemAxis
import gc
import pytest
from .conftest import config
scdoc = "input.scdoc"
step = "input.stp"


class TestPrimitives(BasisTest):
    def setup_class(self):
        BasisTest.setup_class(self, project_name="test_primitives")
        with Scratch(scratch_path) as self.local_scratch:
            #test_primitives_projectfile = os.path.join(self.local_scratch.path, 'test_primitives' + '.aedt')
            #self.aedtapp = Hfss(projectname="Primitives")
            #self.aedtapp.save_project(project_file=test_primitives_projectfile)
            scdoc_file = os.path.join(local_path, 'example_models', scdoc)
            self.local_scratch.copyfile(scdoc_file)
            step_file = os.path.join(local_path, 'example_models', step)
            self.local_scratch.copyfile(step_file)
            test_98_project = os.path.join(local_path, 'example_models', 'assembly2' + '.aedt')
            self.test_98_project = self.local_scratch.copyfile(test_98_project)
            test_99_project = os.path.join(local_path, 'example_models', 'assembly' + '.aedt')
            self.test_99_project = self.local_scratch.copyfile(test_99_project)

    @pyaedt_unittest_check_desktop_error
    def create_copper_box(self, name=None):
        if not name:
            name = "Mybox"
        o = self.aedtapp.modeler.primitives[name]
        if not o:
            o = self.aedtapp.modeler.primitives.create_box([0, 0, 0], [10, 10, 5], name, "Copper")
        return o

    @pyaedt_unittest_check_desktop_error
    def create_copper_sphere(self):
        o = self.aedtapp.modeler.primitives["Mysphere"]
        if not o:
            o = self.aedtapp.modeler.primitives.create_sphere([0, 0, 0], radius="1mm", name="Mysphere", matname="Copper")
        return o

    def create_copper_cylinder(self):
        o = self.aedtapp.modeler.primitives["MyCyl"]
        if not o:
            o = self.aedtapp.modeler.primitives.create_cylinder(cs_axis="Y", position=[20, 20, 0], radius=5, height=20, numSides=8, name="MyCyl", matname="Copper")
        return o

    @pyaedt_unittest_check_desktop_error
    def create_rectangle(self, name=None):
        if not name:
            name = "MyRectangle"
        if not self.aedtapp.modeler.primitives[name]:
            plane = self.aedtapp.CoordinateSystemPlane.XYPlane
            self.aedtapp.modeler.primitives.create_rectangle(plane, [5, 3, 8], [4, 5], name=name)

    @pyaedt_unittest_check_desktop_error
    def create_polylines(self, name=None):
        if not name:
            name = "Poly_"
        if not self.aedtapp.modeler.primitives[name]:
            test_points = [[0, 100, 0],
                           [-100, 0, 0],
                           [-50, -50, 0],
                           [0, 0, 0]]

            p1 = self.aedtapp.modeler.primitives.create_polyline(position_list=test_points,
                                                                 name=name+"segmented")
            p2 = self.aedtapp.modeler.primitives.create_polyline(position_list=test_points,
                                                                 segment_type=["Line", "Arc"],
                                                                 name=name+"compound")
        return p1, p2, test_points

    @pyaedt_unittest_check_desktop_error
    def test_create_box(self):
        udp = self.aedtapp.modeler.Position(0, 0, 0)
        dimensions = [10, 10, 5]
        o = self.aedtapp.modeler.primitives.create_box(udp, dimensions, "Mybox", "Copper")
        assert o.id > 0
        assert o.name == "Mybox"
        assert o.object_type == "Solid"
        assert o.is3d == True
        assert o.material_name == "copper"
        assert "Mybox" in self.aedtapp.modeler.primitives.solids
        assert len(self.aedtapp.modeler.primitives.object_names) == len(self.aedtapp.modeler.primitives.objects)
        pass

    @pyaedt_unittest_check_desktop_error
    def test_create_polyhedron(self):
        o1 = self.aedtapp.modeler.primitives.create_polyhedron()
        assert o1.id > 0
        assert o1.name.startswith("New")
        assert o1.object_type == "Solid"
        assert o1.is3d == True
        assert o1.material_name == "vacuum"
        assert o1.solve_inside

        o2 = self.aedtapp.modeler.primitives.create_polyhedron(cs_axis=CoordinateSystemAxis.ZAxis,
                                                               center_position=[0, 0, 0], start_position=[0, 1, 0],
                                                               height=2.0, num_sides=5, name="MyPolyhedron2",
                                                               matname="Aluminum")
        assert o2.id > 0
        assert o2.name == "MyPolyhedron2"
        assert o2.object_type == "Solid"
        assert o2.is3d == True
        assert o2.material_name == "aluminum"
        assert o2.solve_inside == False

        assert o1.name in self.aedtapp.modeler.primitives.solids
        assert o2.name in self.aedtapp.modeler.primitives.solids
        assert len(self.aedtapp.modeler.primitives.object_names) == len(self.aedtapp.modeler.primitives.objects)
        pass

    @pyaedt_unittest_check_desktop_error
    def test_center_and_centroid(self):
        self.create_copper_box()
        tol = 1e-9
        assert GeometryOperators.v_norm(
            self.aedtapp.modeler.primitives["Mybox"].faces[0].center) - GeometryOperators.v_norm(
            self.aedtapp.modeler.primitives["Mybox"].faces[0].centroid) < tol

    @pyaedt_unittest_check_desktop_error
    def test_01_get_object_name_from_edge(self):
        self.create_copper_box()
        assert self.aedtapp.modeler.get_object_name_from_edge_id(
            self.aedtapp.modeler.primitives["Mybox"].edges[0].id) == "Mybox"

        udp = self.aedtapp.modeler.Position(0, 0, 0)
        dimensions = [10, 10, 5]
        o = self.aedtapp.modeler.primitives.create_box(udp, dimensions)
        assert len(o.name) == 16
        assert o.material_name == "vacuum"

    @pyaedt_unittest_check_desktop_error
    def test_01a_get_faces_from_mat(self):
        faces = self.aedtapp.modeler.select_allfaces_from_mat("Copper")
        assert len(faces)==6

    @pyaedt_unittest_check_desktop_error
    def test_01b_check_object_faces(self):
        self.create_copper_box()
        o = self.aedtapp.modeler.primitives["Mybox"]
        face_list = o.faces
        assert len(face_list) == 6
        f = o.faces[0]
        assert isinstance(f.center, list) and len(f.center) == 3
        assert isinstance(f.area, float) and f.area > 0
        assert o.faces[0].move_with_offset(0.1)
        assert o.faces[0].move_with_vector([0,0,0.01])
        assert type(f.normal) is list

    @pyaedt_unittest_check_desktop_error
    def test_01_check_object_edges(self):
        self.create_copper_box()
        o = self.aedtapp.modeler.primitives["Mybox"]
        e = o.edges[1]
        assert isinstance(e.midpoint, list) and len(e.midpoint) == 3
        assert isinstance(e.length, float) and e.length> 0

    @pyaedt_unittest_check_desktop_error
    def test_01_check_object_vertices(self):
        o = self.aedtapp.modeler.primitives["Mybox"]
        assert len(o.vertices)==8
        v = o.vertices[0]
        assert isinstance(v.position, list) and len(v.position) == 3

    @pyaedt_unittest_check_desktop_error
    def test_02_get_objects_in_group(self):
        objs = self.aedtapp.modeler.get_objects_in_group("Solids")
        assert type(objs) is list

    @pyaedt_unittest_check_desktop_error
    def test_03_create_circle(self):
        udp = self.aedtapp.modeler.Position(5, 3, 8)
        plane = self.aedtapp.CoordinateSystemPlane.XYPlane
        o = self.aedtapp.modeler.primitives.create_circle(plane, udp, 2, name="MyCircle", matname="Copper")
        assert o.id > 0
        assert o.name == "MyCircle"
        assert o.object_type == "Sheet"
        assert o.is3d is False
        assert o.solve_inside is False

    @pyaedt_unittest_check_desktop_error
    def test_04_create_sphere(self):
        udp = self.aedtapp.modeler.Position(20,20, 0)
        radius = 5
        o = self.aedtapp.modeler.primitives.create_sphere(udp, radius, "MySphere", "Copper")
        assert o.id > 0
        assert o.name == "MySphere"
        assert o.object_type == "Solid"
        assert o.is3d is True

    @pyaedt_unittest_check_desktop_error
    def test_05_create_cylinder(self):
        udp = self.aedtapp.modeler.Position(20,20, 0)
        axis = self.aedtapp.CoordinateSystemAxis.YAxis
        radius = 5
        height = 50
        o = self.aedtapp.modeler.primitives.create_cylinder(axis, udp, radius, height, 8, "MyCyl", "Copper")
        assert o.id > 0
        assert o.name == "MyCyl"
        assert o.object_type == "Solid"
        assert o.is3d is True
        pass

    @pyaedt_unittest_check_desktop_error
    def test_06_create_ellipse(self):
        udp = self.aedtapp.modeler.Position(5, 3, 8)
        plane = self.aedtapp.CoordinateSystemPlane.XYPlane
        o1 = self.aedtapp.modeler.primitives.create_ellipse(plane, udp, 5, 1.5, True, name="MyEllpise01", matname="Copper")
        assert o1.id > 0
        assert o1.name == "MyEllpise01"
        assert o1.object_type == "Sheet"
        assert o1.is3d is False
        assert not o1.solve_inside

        o2 = self.aedtapp.modeler.primitives.create_ellipse(plane, udp, 5, 1.5, True, name="MyEllpise01", matname="Vacuum")
        assert o2.id > 0
        assert o2.name.startswith("MyEllpise01")
        assert o2.object_type == "Sheet"
        assert o2.is3d is False
        assert not o2.solve_inside

        o3 = self.aedtapp.modeler.primitives.create_ellipse(plane, udp, 5, 1.5, False, name="MyEllpise02")
        assert o3.id > 0
        assert o3.name == "MyEllpise02"
        assert o3.object_type == "Line"
        assert o3.is3d is False
        assert not o3.solve_inside
        pass

    @pyaedt_unittest_check_desktop_error
    def test_07_create_object_from_edge(self):
        o = self.create_copper_cylinder()
        edges = o.edges
        o = self.aedtapp.modeler.primitives.create_object_from_edge(edges[0])
        assert o.id>0
        assert o.object_type == "Line"
        assert o.is3d is False
        pass

    @pyaedt_unittest_check_desktop_error
    def test_08_create_object_from_face(self):
        o = self.create_copper_cylinder()
        faces = o.faces
        o = self.aedtapp.modeler.primitives.create_object_from_face(faces[0])
        assert o.id > 0
        assert o.object_type == "Sheet"
        assert o.is3d is False
        pass

    @pyaedt_unittest_check_desktop_error
    def test_09_create_polyline(self):
        udp1 = [0, 0, 0]
        udp2 = [5, 0, 0]
        udp3 = [5, 5, 0]
        udp4 = [2, 5, 3]
        arrofpos = [udp1, udp4, udp2, udp3, udp1]
        P = self.aedtapp.modeler.primitives.create_polyline(arrofpos, cover_surface=True, name="Poly1", matname="Copper")
        assert isinstance(P, Polyline)
        assert isinstance(P, Object3d)
        assert P.object_type == "Sheet"
        assert P.is3d == False
        assert isinstance(P.color, tuple)
        get_P = self.aedtapp.modeler.primitives["Poly1"]
        assert isinstance(get_P, Polyline)

    @pyaedt_unittest_check_desktop_error
    def test_10_create_polyline_with_crosssection(self):
        udp1 = [0, 0, 0]
        udp2 = [5, 0, 0]
        udp3 = [5, 5, 0]
        udp4 = [2, 5, 3]
        arrofpos = [udp1, udp2, udp3]
        P = self.aedtapp.modeler.primitives.create_polyline(arrofpos, name="Poly_xsection", xsection_type="Rectangle")
        assert isinstance(P, Polyline)
        assert self.aedtapp.modeler.primitives[P.id].object_type == "Solid"
        assert self.aedtapp.modeler.primitives[P.id].is3d == True

    @pyaedt_unittest_check_desktop_error
    def test_10_sweep_along_path(self):
        udp1 = [0, 0, 0]
        udp2 = [5, 0, 0]
        udp3 = [5, 5, 0]
        arrofpos = [udp1, udp2, udp3]
        my_name = "poly_vector"
        path = self.aedtapp.modeler.primitives.create_polyline(arrofpos, name=my_name)
        assert my_name in self.aedtapp.modeler.primitives.lines
        assert my_name in self.aedtapp.modeler.primitives.model_objects
        assert my_name in self.aedtapp.modeler.primitives.object_names
        assert isinstance(self.aedtapp.modeler.get_vertices_of_line(my_name), list)
        rect = self.aedtapp.modeler.primitives.create_rectangle(self.aedtapp.CoordinateSystemPlane.YZPlane, [0,-2,-2],[4,3], name="rect_1")
        swept = self.aedtapp.modeler.sweep_along_path(rect, path )
        assert swept
        assert rect.name in self.aedtapp.modeler.primitives.solids

    @pyaedt_unittest_check_desktop_error
    def test_10_sweep_along_vector(self):
        rect2 = self.aedtapp.modeler.primitives.create_rectangle(self.aedtapp.CoordinateSystemPlane.YZPlane, [0,-2,-2],[4,3], name="rect_2")
        assert self.aedtapp.modeler.sweep_along_vector(rect2, [10,20,20] )
        assert rect2.name in self.aedtapp.modeler.primitives.solids

    @pyaedt_unittest_check_desktop_error
    def test_11_create_rectangle(self):
        udp = self.aedtapp.modeler.Position(5, 3, 8)
        plane = self.aedtapp.CoordinateSystemPlane.XYPlane
        o = self.aedtapp.modeler.primitives.create_rectangle(plane, udp, [4, 5], name="MyRectangle", matname="Copper")
        assert o.id > 0
        assert o.name == "MyRectangle"
        assert o.object_type == "Sheet"
        assert o.is3d is False

    @pyaedt_unittest_check_desktop_error
    def test_12_create_cone(self):
        udp = self.aedtapp.modeler.Position(5, 3, 8)
        axis = self.aedtapp.CoordinateSystemAxis.ZAxis
        o = self.aedtapp.modeler.primitives.create_cone(axis, udp, 20, 10 ,5 , name="MyCone", matname="Copper")
        assert o.id > 0
        assert o.name == "MyCone"
        assert o.object_type == "Solid"
        assert o.is3d is True

    @pyaedt_unittest_check_desktop_error
    def test_13_get_object_name(self):
        udp = self.aedtapp.modeler.Position(5, 3, 8)
        axis = self.aedtapp.CoordinateSystemAxis.ZAxis
        o = self.aedtapp.modeler.primitives.create_cone(axis, udp, 20, 10, 5, name="MyCone2")
        assert self.aedtapp.modeler.primitives.get_obj_name(o.id) == "MyCone2"
        assert o.name == "MyCone2"

    @pyaedt_unittest_check_desktop_error
    def test_13_get_object_id(self):
        udp = self.aedtapp.modeler.Position(5, 3, 8)
        plane = self.aedtapp.CoordinateSystemPlane.XYPlane
        o = self.aedtapp.modeler.primitives.create_rectangle(plane, udp, [4, 5], name="MyRectangle5")
        assert self.aedtapp.modeler.primitives.get_obj_id("MyRectangle5") == o.id

    @pyaedt_unittest_check_desktop_error
    def test_14_get_object_names(self):

        self.create_polylines()
        self.create_copper_box()
        self.create_rectangle()
        solid_list = self.aedtapp.modeler.primitives.solids
        sheet_list = self.aedtapp.modeler.primitives.sheets
        line_list = self.aedtapp.modeler.primitives.lines
        all_objects_list = self.aedtapp.modeler.primitives.object_names

        assert "Mybox" in solid_list
        assert "MyRectangle" in sheet_list
        assert "Poly_segmented" in line_list
        assert "Poly_compound" in line_list
        assert "Mybox" in all_objects_list
        assert "MyRectangle" in all_objects_list
        assert "Poly_segmented" in all_objects_list
        assert "Poly_compound" in all_objects_list

        print("Solids")
        for solid in solid_list:
            solid_object = self.aedtapp.modeler.primitives[solid]

            print(solid)
            print(solid_object.name)

            assert solid_object.is3d
            assert solid_object.object_type is "Solid"

        print("Sheets")
        for sheet in sheet_list:
            sheet_object = self.aedtapp.modeler.primitives[sheet]
            print(sheet)
            print(sheet_object.name)
            assert self.aedtapp.modeler.primitives[sheet].is3d is False
            assert self.aedtapp.modeler.primitives[sheet].object_type is "Sheet"

        print("Lines")
        for line in line_list:
            line_object = self.aedtapp.modeler.primitives[line]
            print(line)
            print(line_object.name)
            assert self.aedtapp.modeler.primitives[line].is3d is False
            assert self.aedtapp.modeler.primitives[line].object_type is "Line"

        assert len(all_objects_list) == len(solid_list) + len(line_list) + len(sheet_list)

    @pyaedt_unittest_check_desktop_error
    def test_15_get_object_by_material(self):
        self.create_polylines()
        self.create_copper_box()
        self.create_rectangle()
        listsobj = self.aedtapp.modeler.primitives.get_objects_by_material("vacuum")
        assert len(listsobj) > 0
        listsobj = self.aedtapp.modeler.primitives.get_objects_by_material("FR4")
        assert len(listsobj) == 0

    def test_16_get_object_faces(self):
        self.create_rectangle()
        o = self.aedtapp.modeler.primitives["MyRectangle"]
        #listsobj = self.aedtapp.modeler.primitives.get_object_faces("MyRectangl_new")
        assert len(o.faces) == 1
        #listsobj = self.aedtapp.modeler.primitives.get_object_edges("MyRectangl_new")
        assert len(o.edges) == 4
        #listsobj = self.aedtapp.modeler.primitives.get_object_vertices("MyRectangl_new")
        assert len(o.vertices) == 4

    def test_19_get_edges_from_position(self):
        self.aedtapp.odesktop.CloseAllWindows()
        self.aedtapp.oproject.SetActiveDesign(self.aedtapp.odesign.GetName())
        self.create_rectangle()
        o = self.aedtapp.modeler.primitives["MyRectangle"]
        udp = self.aedtapp.modeler.Position(5, 3, 8)
        edge_id = self.aedtapp.modeler.primitives.get_edgeid_from_position(udp, "MyRectangle")
        assert edge_id > 0
        edge_id = self.aedtapp.modeler.primitives.get_edgeid_from_position(udp)
        assert edge_id > 0

    def test_20_get_faces_from_position(self):
        self.aedtapp.odesktop.CloseAllWindows()
        self.aedtapp.oproject.SetActiveDesign(self.aedtapp.odesign.GetName())
        udp = self.aedtapp.modeler.Position(5, 3, 8)
        edge_id = self.aedtapp.modeler.primitives.get_faceid_from_position(udp, "MyRectangl_new")
        assert edge_id>0
        udp = self.aedtapp.modeler.Position(100, 100, 100)
        edge_id = self.aedtapp.modeler.primitives.get_faceid_from_position(udp)
        assert edge_id==-1

    def test_21_delete_object(self):
        self.create_rectangle()
        o = self.aedtapp.modeler.primitives["MyRectangle"]
        deleted = self.aedtapp.modeler.primitives.delete("MyRectangle")
        assert deleted
        assert "MyRectangl_new" not in self.aedtapp.modeler.primitives.object_names

    def test_22_get_face_vertices(self):
        plane = self.aedtapp.CoordinateSystemPlane.XYPlane
        rectid = self.aedtapp.modeler.primitives.create_rectangle(plane, [1, 2, 3], [7, 13], name="rect_for_get")
        listfaces = self.aedtapp.modeler.primitives.get_object_faces("rect_for_get")
        vertices = self.aedtapp.modeler.primitives.get_face_vertices(listfaces[0])
        assert len(vertices) == 4

    def test_23_get_edge_vertices(self):
        listedges = self.aedtapp.modeler.primitives.get_object_edges("rect_for_get")
        vertices = self.aedtapp.modeler.primitives.get_edge_vertices(listedges[0])
        assert len(vertices) == 2


    def test_24_get_vertex_position(self):
        listedges = self.aedtapp.modeler.primitives.get_object_edges("rect_for_get")
        vertices = self.aedtapp.modeler.primitives.get_edge_vertices(listedges[0])
        pos1 = self.aedtapp.modeler.primitives.get_vertex_position(vertices[0])
        assert len(pos1) == 3
        pos2 = self.aedtapp.modeler.primitives.get_vertex_position(vertices[1])
        assert len(pos2) == 3
        edge_length = ( (pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2 + (pos1[2]-pos2[2])**2 )**0.5
        assert edge_length == 7

    def test_25_get_face_area(self):
        listfaces = self.aedtapp.modeler.primitives.get_object_faces("rect_for_get")
        area = self.aedtapp.modeler.primitives.get_face_area(listfaces[0])
        assert area == 7*13

    def test_26_get_face_center(self):
        listfaces = self.aedtapp.modeler.primitives.get_object_faces("rect_for_get")
        center = self.aedtapp.modeler.primitives.get_face_center(listfaces[0])
        assert center == [4.5, 8.5, 3.0]

    def test_27_get_edge_midpoint(self):
        listedges = self.aedtapp.modeler.primitives.get_object_edges("rect_for_get")
        point = self.aedtapp.modeler.primitives.get_edge_midpoint(listedges[0])
        assert point == [4.5, 2.0, 3.0]

    def test_28_get_bodynames_from_position(self):
        center = [20, 20, 0]
        radius = 1
        id = self.aedtapp.modeler.primitives.create_sphere(center, radius, "fred")
        spherename = self.aedtapp.modeler.primitives.get_bodynames_from_position(center)
        assert "fred" in spherename

        plane = self.aedtapp.CoordinateSystemPlane.XYPlane
        rectid = self.aedtapp.modeler.primitives.create_rectangle(plane, [-50, -50, -50], [2, 2], name="bob")
        rectname = self.aedtapp.modeler.primitives.get_bodynames_from_position([-49.0, -49.0, -50.0])
        assert "bob" in rectname

        udp1 = self.aedtapp.modeler.Position(-23, -23, 13)
        udp2 = self.aedtapp.modeler.Position(-27, -27, 11)
        udp3 = self.aedtapp.modeler.Position(-31, -31, 7)
        udp4 = self.aedtapp.modeler.Position(2, 5, 3)
        arrofpos = [udp1, udp2, udp3, udp4]
        P = self.aedtapp.modeler.primitives.create_polyline(arrofpos, cover_surface=False, name="bill")
        polyname = self.aedtapp.modeler.primitives.get_bodynames_from_position([-27, -27, 11])
        assert "bill" in polyname

    def test_29_getobjects_with_strings(self):
        list1 = self.aedtapp.modeler.primitives.get_objects_w_string("MyCone")
        list2 = self.aedtapp.modeler.primitives.get_objects_w_string("my", False)

        assert len(list1) > 0
        assert len(list2) > 0

    def test_30_getmodel_objects(self):
        list1 = self.aedtapp.modeler.primitives.model_objects
        list2 = self.aedtapp.modeler.primitives.non_model_objects
        list3 = self.aedtapp.modeler.primitives.object_names
        for el in list1:
            if el not in list3:
                print("Missing {}".format(el))
        assert len(list1) + len(list2) == len(list3)

    def test_31_create_rect_sheet_to_ground(self):
        id = self.aedtapp.modeler.create_sheet_to_ground("Mybox")
        assert id > 0
        assert self.aedtapp.modeler.create_sheet_to_ground("Mybox", "MyRectangle",self.aedtapp.AxisDir.ZNeg)>0

    def test_31b_get_edges_for_circuit_port(self):
        udp = self.aedtapp.modeler.Position(0, 0, 8)
        plane = self.aedtapp.CoordinateSystemPlane.XYPlane
        id = self.aedtapp.modeler.primitives.create_rectangle(plane, udp, [3, 10], name="MyGND", matname="Copper")
        face_id = self.aedtapp.modeler.primitives["MyRectangle"].faces[0].id
        edges1 = self.aedtapp.modeler.primitives.get_edges_for_circuit_port(face_id, XY_plane=True, YZ_plane=False, XZ_plane=False,
                                                      allow_perpendicular=True, tol=1e-6)
        edges2 = self.aedtapp.modeler.primitives.get_edges_for_circuit_port_from_sheet("MyRectangle", XY_plane=True, YZ_plane=False, XZ_plane=False,
                                                      allow_perpendicular=True, tol=1e-6)

    def test_32_chamfer(self):

        assert self.aedtapp.modeler.chamfer("Mybox", self.aedtapp.modeler.primitives["Mybox"].edges[0])
        self.aedtapp.odesign.Undo()
        assert self.aedtapp.modeler.chamfer("Mybox", self.aedtapp.modeler.primitives["Mybox"].edges[0], chamfer_type=1)
        self.aedtapp.odesign.Undo()
        assert self.aedtapp.modeler.chamfer("Mybox", self.aedtapp.modeler.primitives["Mybox"].edges[0], chamfer_type=2)
        self.aedtapp.odesign.Undo()
        assert self.aedtapp.modeler.chamfer("Mybox", self.aedtapp.modeler.primitives["Mybox"].edges[0], chamfer_type=3)
        self.aedtapp.odesign.Undo()
        assert not self.aedtapp.modeler.chamfer("Mybox", self.aedtapp.modeler.primitives["Mybox"].edges[0], chamfer_type=4)
        assert self.aedtapp.modeler.primitives["Mybox"].edges[0].chamfer()
        self.aedtapp.odesign.Undo()
        assert self.aedtapp.modeler.primitives["Mybox"].edges[0].chamfer(chamfer_type=1)
        self.aedtapp.odesign.Undo()
        assert self.aedtapp.modeler.primitives["Mybox"].edges[0].chamfer(chamfer_type=2)
        self.aedtapp.odesign.Undo()
        assert self.aedtapp.modeler.primitives["Mybox"].edges[0].chamfer(chamfer_type=3)
        self.aedtapp.odesign.Undo()
        assert not self.aedtapp.modeler.primitives["Mybox"].edges[0].chamfer(chamfer_type=5)

    def test_33_fillet(self):

        assert self.aedtapp.modeler.fillet("Mybox", self.aedtapp.modeler.primitives["Mybox"].edges[0])
        self.aedtapp.odesign.Undo()
        assert self.aedtapp.modeler.primitives["Mybox"].edges[0].fillet()
        self.aedtapp.odesign.Undo()

    def test_34_create_polyline_basic_segments(self):
        prim3D = self.aedtapp.modeler.primitives
        self.aedtapp["p1"] = "100mm"
        self.aedtapp["p2"] = "71mm"
        test_points = [["0mm",     "p1",     "0mm"],
                       ["-p1",     "0mm",    "0mm"],
                       ["-p1/2",   "-p1/2",  "0mm"],
                       ["0mm",     "0mm",    "0mm"]]

        assert prim3D.create_polyline(position_list=test_points[0:2], name="PL01_line")
        assert prim3D.create_polyline(position_list=test_points[0:3], segment_type="Arc", name="PL02_arc")

        assert prim3D.create_polyline(position_list=test_points,
                                      segment_type=PolylineSegment("Spline", num_points=4),
                                      name="PL03_spline_4pt")
        assert prim3D.create_polyline(position_list=test_points,
                                      segment_type=PolylineSegment("Spline", num_points=3),
                                      name="PL03_spline_3pt")
        assert prim3D.create_polyline(position_list=test_points[0:3],
                                      segment_type="Spline",
                                      name="PL03_spline_str_3pt")
        assert prim3D.create_polyline(position_list=test_points[0:2],
                                      segment_type="Spline",
                                      name="PL03_spline_str_2pt")
        assert prim3D.create_polyline(position_list=[[100, 100, 0]],
                                      segment_type=PolylineSegment("AngularArc", arc_center=[0, 0, 0], arc_angle="30deg"),
                                      name="PL04_center_point_arc")

    def test_35_create_circle_from_2_arc_segments(self):
        prim3D = self.aedtapp.modeler.primitives
        assert prim3D.create_polyline(position_list=[[34.1004, 14.1248, 0],
                                                     [27.646, 16.7984, 0],
                                                     [24.9725, 10.3439, 0],
                                                     [31.4269, 7.6704, 0]],
                                      segment_type=["Arc", "Arc"],
                                      cover_surface=True, close_surface=True,
                                      name="Rotor_Subtract_25_0", matname="vacuum")

    def test_36_compound_polylines_segments(self):
        prim3D = self.aedtapp.modeler.primitives
        self.aedtapp["p1"] = "100mm"
        self.aedtapp["p2"] = "71mm"
        test_points = [["0mm",     "p1",     "0mm"],
                       ["-p1",     "0mm",    "0mm"],
                       ["-p1/2",   "-p1/2",  "0mm"],
                       ["0mm",     "0mm",    "0mm"]]

        assert prim3D.create_polyline(position_list=test_points, name="PL06_segmented_compound_line")
        assert prim3D.create_polyline(position_list=test_points, segment_type=["Line", "Arc"],
                                      name="PL05_compound_line_arc")
        assert prim3D.create_polyline(position_list=test_points,
                                      close_surface=True,
                                      name="PL07_segmented_compound_line_closed")
        assert prim3D.create_polyline(position_list=test_points,
                                      cover_surface=True,
                                      name="SPL01_segmented_compound_line")

    def test_37_insert_polylines_segments_test1(self):
        self.aedtapp["p1"] = "100mm"
        self.aedtapp["p2"] = "71mm"
        test_points = [["0mm",     "p1",     "0mm"],
                       ["-p1",     "0mm",    "0mm"],
                       ["-p1/2",   "-p1/2",  "0mm"],
                       ["0mm",     "0mm",    "0mm"]]
        P = self.aedtapp.modeler.primitives.create_polyline(position_list=test_points,
                                   close_surface=True,
                                   name="PL08_segmented_compound_insert_segment")
        assert P
        start_point = P.start_point
        insert_point = ["90mm", "20mm", "0mm"]
        assert P.insert_segment(position_list=[start_point, insert_point])

    def test_38_insert_polylines_segments_test2(self):
        prim3D = self.aedtapp.modeler.primitives
        self.aedtapp["p1"] = "100mm"
        self.aedtapp["p2"] = "71mm"
        test_points = [["0mm",     "p1",     "0mm"],
                       ["-p1",     "0mm",    "0mm"],
                       ["-p1/2",   "-p1/2",  "0mm"],
                       ["0mm",     "0mm",    "0mm"]]

        P = prim3D.create_polyline(position_list=test_points,
                                   close_surface=False,
                                   name="PL08_segmented_compound_insert_arc")
        start_point = P.vertex_positions[1]
        insert_point1 = ["90mm", "20mm", "0mm"]
        insert_point2 = [40, 40, 0]

        P.insert_segment(position_list=[start_point, insert_point1, insert_point2], segment="Arc")

    @pyaedt_unittest_check_desktop_error
    def test_39_modify_crossection(self):

        P = self.aedtapp.modeler.primitives.create_polyline(position_list=[[34.1004, 14.1248, 0],
                                                                           [27.646, 16.7984, 0],
                                                                           [24.9725, 10.3439, 0]],
                                                            name="Rotor_Subtract_25_0",
                                                            matname="copper")
        P1 = P.clone()
        P2 = P.clone()
        P3 = P.clone()
        P4 = P.clone()

        P1.set_crosssection_properties(type="Line", width="1mm")
        P2.set_crosssection_properties(type="Circle", width="1mm", num_seg=5)
        P3.set_crosssection_properties(type="Rectangle", width="1mm", height="1mm")
        P4.set_crosssection_properties(type="Isosceles Trapezoid", width="1mm", height="1mm", topwidth="4mm")

        assert self.aedtapp.modeler.primitives.objects[P.id].object_type == "Line"
        assert self.aedtapp.modeler.primitives.objects[P1.id].object_type == "Sheet"
        assert self.aedtapp.modeler.primitives.objects[P2.id].is3d
        assert self.aedtapp.modeler.primitives.objects[P3.id].is3d
        assert self.aedtapp.modeler.primitives.objects[P4.id].is3d
        assert self.aedtapp.modeler.primitives.objects[P2.id].object_type == "Solid"
        assert self.aedtapp.modeler.primitives.objects[P3.id].object_type == "Solid"
        assert self.aedtapp.modeler.primitives.objects[P4.id].object_type == "Solid"

    def test_40_remove_vertex_from_polyline(self):

        p1, p2, test_points = self.create_polylines()

        P = self.aedtapp.modeler.primitives["PL06_segmented_compound_line"]
        P.remove_vertex(test_points[2])

        P1 = self.aedtapp.modeler.primitives.create_polyline([[0, 1, 2], [0, 2, 3], [2, 1, 4]])
        P1.remove_vertex([0, 1, 2])

        P2 = self.aedtapp.modeler.primitives.create_polyline([[0, 1, 2], [0, 2, 3], [2, 1, 4]])
        P2.remove_vertex(["0mm", "1mm", "2mm"])

        P3 = self.aedtapp.modeler.primitives.create_polyline([[0, 1, 2], [0, 2, 3], [2, 1, 4]])
        P3.remove_vertex(["0mm", "1mm", "2mm"], abstol=1e-6)

    def test_41_remove_edges_from_polyline(self):

        primitives = self.aedtapp.modeler.primitives
        P = primitives.create_polyline([[0, 1, 2], [0, 2, 3], [2, 1, 4]])
        P.remove_edges(edge_id=0)
        P = primitives.create_polyline([[0, 1, 2], [0, 2, 3], [2, 1, 4]])
        P.remove_edges(edge_id=[0, 1])


    def test_42_duplicate_polyline_and_manipulate(self):

        primitives = self.aedtapp.modeler.primitives
        P1 = primitives.create_polyline([[0, 1, 2], [0, 2, 3], [2, 1, 4]])
        P2 = P1.clone()

        assert P2.id != P1.id

    def test_43_create_bond_wires(self):

        b1 = self.aedtapp.modeler.primitives.create_bondwire([0,0,0], [10,10,2], h1=0.15, h2=0, diameter=0.034, facets=8, matname="copper", name="jedec51")
        assert b1
        b2 = self.aedtapp.modeler.primitives.create_bondwire([0,0,0], [10,10,2], h1=0.15, h2=0, diameter=0.034, bond_type=1,  matname="copper", name="jedec41")
        assert b2
        b2 = self.aedtapp.modeler.primitives.create_bondwire([0,0,0], [10,10,2], h1=0.15, h2=0, diameter=0.034, bond_type=2,  matname="copper", name="jedec41")
        assert b2
        b2 = self.aedtapp.modeler.primitives.create_bondwire([0,0,0], [10,10,2], h1=0.15, h2=0, diameter=0.034, bond_type=3,  matname="copper", name="jedec41")
        assert b2 == False

    def test_44_create_group(self):
        assert self.aedtapp.modeler.create_group(["jedec51","jedec41"],"mygroup")
        assert self.aedtapp.modeler.ungroup("mygroup")

    def test_45_flatten_assembly(self):
        assert self.aedtapp.modeler.flatten_assembly()

    def test_46_solving_volume(self):
        vol = self.aedtapp.modeler.get_solving_volume()
        assert len(vol) == 9

    def test_46_lines(self):
        assert self.aedtapp.modeler.vertex_data_of_lines()

    def test_47_get_edges_on_bounding_box(self):
        self.aedtapp.close_project(name=self.aedtapp.project_name, saveproject=False)
        self.aedtapp.load_project(self.test_99_project)
        self.aedtapp.modeler.primitives.refresh_all_ids()
        edges = self.aedtapp.modeler.primitives.get_edges_on_bounding_box(['Port1', 'Port2'], return_colinear=True, tol=1e-6)
        assert edges == [5219, 5183]
        edges = self.aedtapp.modeler.primitives.get_edges_on_bounding_box(['Port1', 'Port2'], return_colinear=False, tol=1e-6)
        assert edges == [5237, 5255, 5273, 5291]

    def test_48_get_closest_edge_to_position(self):
        self.aedtapp.modeler.primitives.get_closest_edgeid_to_position([0.2,0,0])

    @pytest.mark.skipif(config["skip_space_claim"] == True or config["build_machine"] == True,
                        reason="Skipped because SpaceClaim is not installed on Build Machine")
    def test_48_import_space_claim(self):
        self.aedtapp.insert_design("SCImport")
        assert self.aedtapp.modeler.import_spaceclaim_document(os.path.join(self.local_scratch.path, scdoc))
        assert len(self.aedtapp.modeler.primitives.objects) == 1

    def test_49_import_step(self):
        self.aedtapp.insert_design("StepImport")
        assert self.aedtapp.modeler.import_3d_cad(os.path.join(self.local_scratch.path, step))
        assert len(self.aedtapp.modeler.primitives.objects) == 1
        pass