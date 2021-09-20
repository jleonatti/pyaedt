"""
This module contains the `Materials` class.
"""
from __future__ import absolute_import

import json

from ..generic.DataHandlers import arg2dict
from pyaedt.generic.general_methods import aedt_exception_handler, retry_ntimes, generate_unique_name
from pyaedt.modules.Material import Material, SurfaceMaterial, MatProperties, OrderedDict


class Materials(object):
    """Contains the AEDT materials database and all methods for creating and editing materials.

    Parameters
    ----------
    parent : str
        Inherited parent object.

    """

    @property
    def odefinition_manager(self):
        """Definition manager."""
        return self._parent._oproject.GetDefinitionManager()

    @property
    def omaterial_manager(self):
        """Material manager."""
        return self.odefinition_manager.GetManager("Material")

    @property
    def _messenger(self):
        """Messenger.

        Returns
        -------
        MessageManager
            Message manager object.
        """
        return self._parent._messenger

    @property
    def logger(self):
        """Logger."""
        return self._parent.logger

    @property
    def oproject(self):
        """Project."""
        return self._parent.oproject

    def __init__(self, parent):
        self._parent = parent
        self._messenger.logger.info("Successfully loaded project materials !")
        self.material_keys = self._get_materials()
        self.surface_material_keys = self._get_surface_materials()
        self._load_from_project()
        pass

    def __len__(self):
        return len(self.material_keys)

    def __iter__(self):
        return self.material_keys.itervalues()

    def __getitem__(self, item):
        item = item.lower()
        if item in list(self.material_keys.keys()):
            return self.material_keys[item]
        elif item in list(self.surface_material_keys.keys()):
            return self.surface_material_keys[item]

    @aedt_exception_handler
    def _get_materials(self):
        """Get materials."""
        mats = {}
        try:
            for ds in self._parent.project_properies["AnsoftProject"]["Definitions"]["Materials"]:
                mats[ds.lower()] = Material(
                    self, ds.lower(), self._parent.project_properies["AnsoftProject"]["Definitions"]["Materials"][ds]
                )
        except:
            pass
        return mats

    @aedt_exception_handler
    def _get_surface_materials(self):
        mats = {}
        try:
            for ds in self._parent.project_properies["AnsoftProject"]["Definitions"]["SurfaceMaterials"]:
                mats[ds.lower()] = SurfaceMaterial(
                    self,
                    ds.lower(),
                    self._parent.project_properies["AnsoftProject"]["Definitions"]["SurfaceMaterials"][ds],
                )
        except:
            pass
        return mats

    @aedt_exception_handler
    def checkifmaterialexists(self, mat):
        """Check if a material exists in AEDT.

        Parameters
        ----------
        mat : str
            Name of the material. If the material exists and is not in the materials database,
            it is added to this database.

        Returns
        -------
        bool
            ``True`` when successful, ``False`` when failed.

        """
        mat = mat.lower()
        lista = [i.lower() for i in list(self.odefinition_manager.GetProjectMaterialNames())]
        if mat in lista:
            return True
        else:
            mattry = self.omaterial_manager.GetData(mat)
            if mattry:
                self._aedmattolibrary(mat)
                return True
            else:
                return False

    @aedt_exception_handler
    def check_thermal_modifier(self, mat):
        """Check a material to see if it has any thermal modifiers.

        Parameters
        ----------
        mat : str
            Name of the material. All properties for this material are checked
            for thermal modifiers.

        Returns
        -------
        bool
            ``True`` when successful, ``False`` when failed.

        """
        mat = mat.lower()
        exists = False
        if mat in self.material_keys:
            exists = True
        elif self.checkifmaterialexists(mat):
            self._load_from_project()
            exists = True
        if exists:
            omat = self.material_keys[mat]
            for el in MatProperties.aedtname:
                if omat.__dict__["_" + el].thermalmodifier:
                    return True
        return False

    @aedt_exception_handler
    def add_material(self, materialname, props=None):
        """Add a material with default values.

        When the added material object is returned, you can customize
        the material. This method does not update the material.

        Parameters
        ----------
        materialname : str
            Name of the material.
        props : dict, optional
            Material property dictionary. The default is ``None``.

        Returns
        -------
        :class:`pyaedt.modules.Material.Material`

        Examples
        --------

        >>> from pyaedt import Hfss
        >>> hfss = Hfss()
        >>> mat = hfss.materials.add_material("MyMaterial")
        >>> print(mat.conductivity.value)

        """
        materialname = materialname.lower()
        self.logger.global_logger.info("Adding new material to the Project Library: " + materialname)
        if materialname in self.material_keys:
            self.logger.global_logger.warning(
                "Warning. The material is already in the database. Change or edit the name."
            )
            return self.material_keys[materialname]
        else:
            material = Material(self._parent, materialname, props)
            material.update()
            self.logger.global_logger.info("Material has been added. Edit it to update in Desktop.")
            self.material_keys[materialname] = material
            return self.material_keys[materialname]

    @aedt_exception_handler
    def add_surface_material(self, material_name, emissivity=None):
        """Add a surface material.

        In AEDT, base properties are loaded from the XML database file ``amat.xml``
        or from the emissivity.

        Parameters
        ----------
        material_name : str
            Name of the surface material.
        emissivity : float, optional
            Emissivity value.

        Returns
        -------
        :class:`pyaedt.modules.SurfaceMaterial`

        Examples
        --------

        >>> from pyaedt import Hfss
        >>> hfss = Hfss()
        >>> mat = hfss.materials.add_surface_material("Steel", 0.85)
        >>> print(mat.emissivity.value)
        """

        materialname = material_name.lower()
        self.logger.global_logger.info("Adding a surface material to the project library: " + materialname)
        if materialname in self.surface_material_keys:
            self.logger.global_logger.warning(
                "Warning. The material is already in the database. Change the name or edit it."
            )
            return self.surface_material_keys[materialname]
        else:
            material = SurfaceMaterial(self._parent, materialname)
            if emissivity:
                material.emissivity = emissivity
                material.update()
            self.logger.global_logger.info("Material has been added. Edit it to update in Desktop.")
            self.surface_material_keys[materialname] = material
            return self.surface_material_keys[materialname]

    @aedt_exception_handler
    def _create_mat_project_vars(self, matlist):
        matprop = {}
        tol = 1e-12
        for prop in MatProperties.aedtname:
            matprop[prop] = []
            for mat in matlist:
                try:
                    matprop[prop].append(float(mat.__dict__["_" + prop].value))
                except:
                    self.logger.global_logger.warning("Warning. Wrong parsed property. Reset to 0")
                    matprop[prop].append(0)
            try:
                a = sum(matprop[prop])
                if a < tol:
                    del matprop[prop]
            except:
                pass
        return matprop

    @aedt_exception_handler
    def add_material_sweep(self, swargs, matname):
        """Create a sweep material made of an array of materials.

        If a material needs to have a dataset (thermal modifier), then a
        dataset is created. Material properties are loaded from the XML file
        database ``amat.xml``.

        Parameters
        ----------
        swargs : list
            List of materials to merge into a single sweep material.
        matname : str
            Name of the sweep material.
        enableTM : bool, optional
            Unavailable currently. Whether to enable the thermal modifier.
            The default is ``True``.

        Returns
        -------
        int
            Index of the project variable.

        Examples
        --------

        >>> from pyaedt import Hfss
        >>> hfss = Hfss()
        >>> hfss.materials.add_material("MyMaterial")
        >>> hfss.materials.add_material("MyMaterial2")
        >>> hfss.materials.add_material_sweep(["MyMaterial", "MyMaterial2"], "Sweep_copper")

        """
        matsweep = []
        matname = matname.lower()
        for args in swargs:
            if args.lower() in [i.lower() for i in self.material_keys.keys()]:
                matsweep.append(self.material_keys[args.lower()])
            elif self.checkifmaterialexists(args):
                self._aedmattolibrary(args)
                matsweep.append(self.material_keys[args.lower()])

        mat_dict = self._create_mat_project_vars(matsweep)

        newmat = Material(self._parent, matname)
        index = "$ID" + matname
        self._parent[index] = 0
        for el in mat_dict:
            if el in list(mat_dict.keys()):
                self._parent["$" + matname + el] = mat_dict[el]
                newmat.__dict__["_" + el].value = "$" + matname + el + "[" + index + "]"
                newmat._update_props(el, "$" + matname + el + "[" + index + "]", False)

        newmat.update()
        self.material_keys[matname] = newmat
        return index

    @aedt_exception_handler
    def duplicate_material(self, material, new_name):
        """Duplicate a material.

        Parameters
        ----------
        material : str
            Name of the material.
        new_name : str
            Name for the copy of the material.

        Returns
        -------
        :class:`pyaedt.modules.Material.Material`

        Examples
        --------

        >>> from pyaedt import Hfss
        >>> hfss = Hfss()
        >>> hfss.materials.add_material("MyMaterial")
        >>> hfss.materials.duplicate_material("MyMaterial", "MyMaterial2")

        """
        if material.lower() not in list(self.material_keys.keys()):
            self._messenger.add_error_message("Material {} is not present".format(material))
            return False
        newmat = Material(self, new_name.lower(), self.material_keys[material.lower()]._props)
        newmat.update()
        self.material_keys[new_name.lower()] = newmat
        return newmat

    @aedt_exception_handler
    def duplicate_surface_material(self, material, new_name):
        """Duplicate a surface material.

        Parameters
        ----------
         material : str
            Name of the surface material.
        new_name : str
            Name for the copy of the surface material.

        Returns
        -------
        :class:`pyaedt.modules.SurfaceMaterial`

        Examples
        --------

        >>> from pyaedt import Hfss
        >>> hfss = Hfss()
        >>> hfss.materials.add_surface_material("MyMaterial")
        >>> hfss.materials.duplicate_surface_material("MyMaterial", "MyMaterial2")

        """
        if not material.lower() in list(self.surface_material_keys.keys()):
            self._messenger.add_error_message("Material {} is not present".format(material))
            return False
        newmat = SurfaceMaterial(self, new_name.lower(), self.surface_material_keys[material.lower()]._props)
        newmat.update()
        self.surface_material_keys[new_name.lower()] = newmat
        return newmat

    @aedt_exception_handler
    def remove_material(self, material, library="Project"):
        """Remove a material.

        Parameters
        ----------
        material : str
            Name of the material.
        library : str, optional
            Name of the library containing this material.
            The default is ``"Project"``.

        Returns
        -------
        bool
            ``True`` when successful, ``False`` when failed.


        Examples
        --------

        >>> from pyaedt import Hfss
        >>> hfss = Hfss()
        >>> hfss.materials.add_material("MyMaterial")
        >>> hfss.materials.remove_material("MyMaterial")

        """
        if material not in list(self.material_keys.keys()):
            self._messenger.add_error_message("Material {} is not present".format(material))
            return False
        self.odefinition_manager.RemoveMaterial(material, True, "", library)
        del self.material_keys[material]
        return True

    @property
    def conductors(self):
        """Conductors in the material database.

        Returns
        -------
        list
            List of conductors in the material database.

        """
        data = []
        for key, mat in self.material_keys.items():
            if mat.is_conductor():
                data.append(key)
        return data

    @property
    def dielectrics(self):
        """Dielectrics in the material database.

        Returns
        -------
        list
            List of dielctrics in the material database.

        """
        data = []
        for key, mat in self.material_keys.items():
            if mat.is_dielectric():
                data.append(key)
        return data

    def _load_from_project(self):
        mats = self.odefinition_manager.GetProjectMaterialNames()
        for el in mats:
            if el not in list(self.material_keys.keys()):
                try:
                    self._aedmattolibrary(el)
                except Exception as e:
                    self.logger.global_logger.info("aedmattolibrary failed for material {}".format(el))

    @aedt_exception_handler
    def _aedmattolibrary(self, matname):
        matname = matname.lower()
        props = {}
        arg2dict(list(retry_ntimes(10, self.omaterial_manager.GetData, matname)), props)
        values_view = props.values()
        value_iterator = iter(values_view)
        first_value = next(value_iterator)
        newmat = Material(self, matname, first_value)

        self.material_keys[matname] = newmat
        return True

    def export_materials_to_file(self, full_json_path):
        """Export all materials to a JSON file.

        Parameters
        ----------
        full_json_path : str
            Full path and name of the JSON file to export to.

        Returns
        -------
        bool
            ``True`` when successful, ``False`` when failed.

        """

        def find_datasets(d, out_list):
            for k, v in d.items():
                if isinstance(v, dict):
                    find_datasets(v, out_list)
                else:
                    if "pwl(" in str(v):
                        out_list.append(v[v.find("$") : v.find(",")])

        # Data to be written
        output_dict = OrderedDict()
        for el, val in self.material_keys.items():
            output_dict[el] = val._props
        out_list = []
        find_datasets(output_dict, out_list)
        datasets = OrderedDict()
        for ds in out_list:
            if ds in list(self._parent.project_datasets.keys()):
                d = self._parent.project_datasets[ds]
                if d.z:
                    datasets[ds] = OrderedDict(
                        {
                            "Coordinates": OrderedDict(
                                {
                                    "DimUnits": [d.xunit, d.yunit, d.zunit],
                                    "Points": [val for tup in zip(d.x, d.y, d.z) for val in tup],
                                }
                            )
                        }
                    )
                else:
                    datasets[ds] = OrderedDict(
                        {
                            "Coordinates": OrderedDict(
                                {
                                    "DimUnits": [d.xunit, d.yunit],
                                    "Points": [val for tup in zip(d.x, d.y) for val in tup],
                                }
                            )
                        }
                    )
        json_dict = {}
        json_dict["materials"] = output_dict
        if datasets:
            json_dict["datasets"] = datasets

        with open(full_json_path, "w") as fp:
            json.dump(json_dict, fp, indent=4)
        return True

    def import_materials_from_file(self, full_json_path):
        """Import and create materials from a JSON file.

        Parameters
        ----------
        full_json_path : str
            Full path and name for the JSON file.

        Returns
        -------
        bool
            ``True`` when successful, ``False`` when failed.

        """
        with open(full_json_path) as json_file:
            data = json.load(json_file)

        if "datasets" in list(data.keys()):
            for el, val in data["datasets"].items():
                numcol = len(val["Coordinates"]["DimUnits"])
                xunit = val["Coordinates"]["DimUnits"][0]
                yunit = val["Coordinates"]["DimUnits"][1]
                zunit = ""

                new_list = [
                    val["Coordinates"]["Points"][i : i + numcol]
                    for i in range(0, len(val["Coordinates"]["Points"]), numcol)
                ]
                xval = new_list[0]
                yval = new_list[1]
                zval = None
                if numcol > 2:
                    zunit = val["Coordinates"]["DimUnits"][2]
                    zval = new_list[2]
                self._parent.create_dataset(
                    el[1:], xunit=xunit, yunit=yunit, zunit=zunit, xlist=xval, ylist=yval, zlist=zval
                )

        for el, val in data["materials"].items():
            if el.lower() in list(self.material_keys.keys()):
                newname = generate_unique_name(el)
                self.logger.global_logger.warning("Material {} already exists. Renaming to {}".format(el, newname))
            else:
                newname = el
            newmat = Material(self, newname, val)
            newmat.update()
            self.material_keys[newname] = newmat
        return True
