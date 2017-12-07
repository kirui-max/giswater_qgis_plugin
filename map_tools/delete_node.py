"""
/***************************************************************************
        begin                : 2016-01-05
        copyright            : (C) 2016 by BGEO SL
        email                : vicente.medina@gits.ws
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

"""

# -*- coding: utf-8 -*-
from qgis.core import QgsPoint, QgsFeatureRequest
from PyQt4.QtCore import QPoint, Qt

from map_tools.parent import ParentMapTool


class DeleteNodeMapTool(ParentMapTool):
    """ Button 17: User select one node. Execute SQL function: 'gw_fct_delete_node' """

    def __init__(self, iface, settings, action, index_action):
        """ Class constructor """

        # Call ParentMapTool constructor
        super(DeleteNodeMapTool, self).__init__(iface, settings, action, index_action)



    """ QgsMapTools inherited event functions """

    def canvasMoveEvent(self, event):
        
        # Make sure active layer is always 'v_edit_node'
        cur_layer = self.iface.activeLayer()
        if cur_layer != self.layer_node:
            self.iface.setActiveLayer(self.layer_node) 
          
        # Hide highlight
        self.vertex_marker.hide()
  
        try:
            # Get current mouse coordinates
            x = event.pos().x()
            y = event.pos().y()
            event_point = QPoint(x, y)
        except(TypeError, KeyError):
            self.iface.actionPan().trigger()
            return

        # Snapping
        (retval, result) = self.snapper.snapToCurrentLayer(event_point, 2)  # @UnusedVariable
  
        # That's the snapped features
        if result:          
            # Get the point and add marker on it
            point = QgsPoint(result[0].snappedVertex)
            self.vertex_marker.setCenter(point)
            self.vertex_marker.show()
                

    def canvasReleaseEvent(self, event):

        if event.button() != Qt.LeftButton:
            return

        # Get the click
        x = event.pos().x()
        y = event.pos().y()
        event_point = QPoint(x, y)
        snapped_feat = None

        # Snapping
        (retval, result) = self.snapper.snapToCurrentLayer(event_point, 2)  # @UnusedVariable
            
        # That's the snapped features
        if result:
            # Get the point
            snapped_feat = result[0]
            point = QgsPoint(snapped_feat.snappedVertex)   #@UnusedVariable
            snapped_feat = next(snapped_feat.layer.getFeatures(QgsFeatureRequest().setFilterFid(result[0].snappedAtGeometry)))

        if snapped_feat:

            # Ask for confirmation before executing
            message = ("The procedure will delete features on database. Please ensure that features has no undelete value on true.\n" 
                       "On the other hand you must know that traceability table will storage precedent information.\n"
                       "Are you sure?")
            answer = self.controller.ask_question(message, "Delete node")
            if answer:                
                # Execute SQL function and show result to the user
                function_name = "gw_fct_arc_fusion"
                row = self.controller.check_function(function_name)
                if not row:
                    function_name = "gw_fct_delete_node"
                    row = self.controller.check_function(function_name)
                    if not row:
                        message = "Database function not found"
                        self.controller.show_warning(message, parameter=function_name)
                        return                
                node_id = snapped_feat.attribute('node_id')
                sql = "SELECT " + self.schema_name + "." + function_name + "('" + str(node_id) + "');"
                status = self.controller.execute_sql(sql)
                if status:
                    message = "Node deleted successfully"
                    self.controller.show_info(message)  

                # Refresh map canvas
                self.refresh_map_canvas()


    def activate(self):

        # Check button
        self.action().setChecked(True)

        # Store user snapping configuration
        self.snapper_manager.store_snapping_options()

        # Clear snapping
        self.snapper_manager.clear_snapping()

        # Set active layer to 'v_edit_node'
        self.layer_node = self.controller.get_layer_by_tablename("v_edit_node")
        self.iface.setActiveLayer(self.layer_node)            

        # Change cursor
        self.canvas.setCursor(self.cursor)

        # Show help message when action is activated
        if self.show_help:
            message = "Select the node inside a pipe by clicking on it and it will be removed"
            self.controller.show_info(message)
            


    def deactivate(self):

        # Call parent method     
        ParentMapTool.deactivate(self)
    
