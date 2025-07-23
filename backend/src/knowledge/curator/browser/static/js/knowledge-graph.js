/**
 * Knowledge Graph Visualization using D3.js
 */

(function($) {
    'use strict';

    window.KnowledgeGraph = {
        
        /**
         * Initialize the knowledge graph visualization
         */
        init: function(containerId, options) {
            this.container = d3.select('#' + containerId);
            this.options = $.extend({
                width: 1200,
                height: 800,
                nodeRadius: 10,
                linkDistance: 100,
                charge: -300,
                gravity: 0.05,
                nodeColors: {
                    'ResearchNote': '#3498db',
                    'LearningGoal': '#2ecc71',
                    'ProjectLog': '#e74c3c',
                    'BookmarkPlus': '#f39c12',
                    'Concept': '#9b59b6',
                    'Tag': '#1abc9c',
                    'Person': '#34495e',
                    'Organization': '#95a5a6'
                }
            }, options);
            
            this.setupVisualization();
            this.loadData();
        },
        
        /**
         * Setup D3 visualization components
         */
        setupVisualization: function() {
            // Clear existing content
            this.container.html('');
            
            // Create SVG
            this.svg = this.container.append('svg')
                .attr('width', this.options.width)
                .attr('height', this.options.height)
                .attr('class', 'knowledge-graph-svg');
                
            // Create zoom behavior
            this.zoom = d3.behavior.zoom()
                .scaleExtent([0.1, 10])
                .on('zoom', this.zoomed.bind(this));
                
            // Create main group for zoom/pan
            this.g = this.svg.append('g')
                .call(this.zoom);
                
            // Background for pan
            this.g.append('rect')
                .attr('class', 'graph-background')
                .attr('width', this.options.width * 10)
                .attr('height', this.options.height * 10)
                .attr('transform', 'translate(' + (-this.options.width * 5) + ',' + (-this.options.height * 5) + ')')
                .style('fill', 'none')
                .style('pointer-events', 'all');
                
            // Groups for graph elements
            this.linkGroup = this.g.append('g').attr('class', 'links');
            this.nodeGroup = this.g.append('g').attr('class', 'nodes');
            
            // Force layout
            this.force = d3.layout.force()
                .size([this.options.width, this.options.height])
                .linkDistance(this.options.linkDistance)
                .charge(this.options.charge)
                .gravity(this.options.gravity)
                .on('tick', this.tick.bind(this));
                
            // Tooltip
            this.tooltip = d3.select('body').append('div')
                .attr('class', 'graph-tooltip')
                .style('opacity', 0);
                
            // Add controls
            this.addControls();
        },
        
        /**
         * Add graph controls
         */
        addControls: function() {
            var controls = this.container.append('div')
                .attr('class', 'graph-controls');
                
            // Layout selector
            controls.append('select')
                .attr('id', 'layout-selector')
                .on('change', this.changeLayout.bind(this))
                .selectAll('option')
                .data(['force', 'radial', 'hierarchical', 'circular'])
                .enter().append('option')
                .text(function(d) { return d.charAt(0).toUpperCase() + d.slice(1); })
                .attr('value', function(d) { return d; });
                
            // Filter controls
            var filters = controls.append('div')
                .attr('class', 'graph-filters');
                
            // Node type filters
            var nodeTypes = Object.keys(this.options.nodeColors);
            filters.append('span').text('Filter by type: ');
            
            var typeFilters = filters.selectAll('.type-filter')
                .data(nodeTypes)
                .enter().append('label')
                .attr('class', 'type-filter');
                
            typeFilters.append('input')
                .attr('type', 'checkbox')
                .attr('checked', true)
                .attr('value', function(d) { return d; })
                .on('change', this.filterNodes.bind(this));
                
            typeFilters.append('span')
                .text(function(d) { return ' ' + d + ' '; })
                .style('color', function(d) { return this.options.nodeColors[d]; }.bind(this));
                
            // Search box
            controls.append('input')
                .attr('type', 'text')
                .attr('placeholder', 'Search nodes...')
                .attr('class', 'graph-search')
                .on('keyup', this.searchNodes.bind(this));
                
            // Zoom controls
            var zoomControls = controls.append('div')
                .attr('class', 'zoom-controls');
                
            zoomControls.append('button')
                .text('+')
                .on('click', this.zoomIn.bind(this));
                
            zoomControls.append('button')
                .text('-')
                .on('click', this.zoomOut.bind(this));
                
            zoomControls.append('button')
                .text('Reset')
                .on('click', this.resetZoom.bind(this));
        },
        
        /**
         * Load graph data
         */
        loadData: function() {
            var self = this;
            
            // Get context URL from page
            var contextUrl = $('body').data('context-url') || '';
            
            $.ajax({
                url: contextUrl + '/@@knowledge-graph/visualize',
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    self.processData(data);
                },
                error: function(xhr, status, error) {
                    console.error('Failed to load graph data:', error);
                    self.container.append('<div class="error">Failed to load graph data</div>');
                }
            });
        },
        
        /**
         * Process and render graph data
         */
        processData: function(data) {
            this.graphData = data.graph;
            this.visualizationConfig = data.visualization;
            
            // Update force layout settings if provided
            if (this.visualizationConfig) {
                if (this.visualizationConfig.force) {
                    this.force
                        .charge(this.visualizationConfig.force.charge || this.options.charge)
                        .linkDistance(this.visualizationConfig.force.linkDistance || this.options.linkDistance)
                        .gravity(this.visualizationConfig.force.gravity || this.options.gravity);
                }
            }
            
            this.renderGraph();
        },
        
        /**
         * Render the graph
         */
        renderGraph: function() {
            var self = this;
            
            // Set nodes and links
            this.force
                .nodes(this.graphData.nodes)
                .links(this.graphData.edges);
                
            // Create links
            this.links = this.linkGroup.selectAll('.link')
                .data(this.graphData.edges);
                
            this.links.enter().append('line')
                .attr('class', 'link')
                .style('stroke', function(d) { return d.color || '#999'; })
                .style('stroke-width', function(d) { return d.width || 1; })
                .style('stroke-opacity', 0.6);
                
            // Create nodes
            this.nodes = this.nodeGroup.selectAll('.node')
                .data(this.graphData.nodes);
                
            var nodeEnter = this.nodes.enter().append('g')
                .attr('class', 'node')
                .call(this.force.drag)
                .on('mouseover', this.nodeMouseOver.bind(this))
                .on('mouseout', this.nodeMouseOut.bind(this))
                .on('click', this.nodeClick.bind(this));
                
            // Node circles
            nodeEnter.append('circle')
                .attr('r', function(d) { return d.size || self.options.nodeRadius; })
                .style('fill', function(d) { return d.color || self.options.nodeColors[d.type] || '#95a5a6'; })
                .style('stroke', '#fff')
                .style('stroke-width', 2);
                
            // Node labels
            nodeEnter.append('text')
                .attr('dx', 12)
                .attr('dy', '.35em')
                .text(function(d) { return d.title; })
                .style('font-size', '12px')
                .style('fill', '#333');
                
            // Start force simulation
            this.force.start();
        },
        
        /**
         * Force layout tick function
         */
        tick: function() {
            this.links
                .attr('x1', function(d) { return d.source.x; })
                .attr('y1', function(d) { return d.source.y; })
                .attr('x2', function(d) { return d.target.x; })
                .attr('y2', function(d) { return d.target.y; });
                
            this.nodes
                .attr('transform', function(d) {
                    return 'translate(' + d.x + ',' + d.y + ')';
                });
        },
        
        /**
         * Zoom behavior
         */
        zoomed: function() {
            this.g.attr('transform', 'translate(' + d3.event.translate + ')scale(' + d3.event.scale + ')');
        },
        
        /**
         * Zoom controls
         */
        zoomIn: function() {
            var scale = this.zoom.scale() * 1.2;
            this.zoom.scale(scale);
            this.g.transition().duration(350)
                .attr('transform', 'translate(' + this.zoom.translate() + ')scale(' + scale + ')');
        },
        
        zoomOut: function() {
            var scale = this.zoom.scale() / 1.2;
            this.zoom.scale(scale);
            this.g.transition().duration(350)
                .attr('transform', 'translate(' + this.zoom.translate() + ')scale(' + scale + ')');
        },
        
        resetZoom: function() {
            this.zoom.scale(1);
            this.zoom.translate([0, 0]);
            this.g.transition().duration(350)
                .attr('transform', 'translate(0,0)scale(1)');
        },
        
        /**
         * Node interaction handlers
         */
        nodeMouseOver: function(d) {
            // Highlight connected nodes and links
            var connectedNodes = {};
            connectedNodes[d.id] = true;
            
            this.links.each(function(l) {
                if (l.source.id === d.id) {
                    connectedNodes[l.target.id] = true;
                } else if (l.target.id === d.id) {
                    connectedNodes[l.source.id] = true;
                }
            });
            
            // Fade non-connected elements
            this.nodes.style('opacity', function(n) {
                return connectedNodes[n.id] ? 1 : 0.3;
            });
            
            this.links.style('opacity', function(l) {
                return (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.1;
            });
            
            // Show tooltip
            this.tooltip.transition()
                .duration(200)
                .style('opacity', .9);
                
            var tooltipHtml = '<strong>' + d.title + '</strong><br/>' +
                            'Type: ' + d.type + '<br/>' +
                            'Connections: ' + (d.size - 10) / 2;
                            
            if (d.description) {
                tooltipHtml += '<br/>' + d.description;
            }
            
            this.tooltip.html(tooltipHtml)
                .style('left', (d3.event.pageX + 10) + 'px')
                .style('top', (d3.event.pageY - 28) + 'px');
        },
        
        nodeMouseOut: function(d) {
            // Reset opacity
            this.nodes.style('opacity', 1);
            this.links.style('opacity', 0.6);
            
            // Hide tooltip
            this.tooltip.transition()
                .duration(500)
                .style('opacity', 0);
        },
        
        nodeClick: function(d) {
            // Navigate to node URL if available
            if (d.url) {
                window.location.href = d.url;
            }
        },
        
        /**
         * Change graph layout
         */
        changeLayout: function() {
            var layout = d3.select('#layout-selector').property('value');
            
            switch(layout) {
                case 'radial':
                    this.applyRadialLayout();
                    break;
                case 'hierarchical':
                    this.applyHierarchicalLayout();
                    break;
                case 'circular':
                    this.applyCircularLayout();
                    break;
                default:
                    this.force.start();
            }
        },
        
        /**
         * Apply radial layout
         */
        applyRadialLayout: function() {
            var self = this;
            
            // Find most connected node as center
            var maxConnections = 0;
            var centerNode = null;
            
            this.graphData.nodes.forEach(function(node) {
                var connections = 0;
                self.graphData.edges.forEach(function(edge) {
                    if (edge.source.id === node.id || edge.target.id === node.id) {
                        connections++;
                    }
                });
                
                if (connections > maxConnections) {
                    maxConnections = connections;
                    centerNode = node;
                }
            });
            
            if (!centerNode) return;
            
            // Position center node
            centerNode.x = this.options.width / 2;
            centerNode.y = this.options.height / 2;
            centerNode.fixed = true;
            
            // Position other nodes in circles
            var visited = {};
            visited[centerNode.id] = true;
            
            var rings = [[centerNode]];
            var currentRing = [centerNode];
            
            while (Object.keys(visited).length < this.graphData.nodes.length) {
                var nextRing = [];
                
                currentRing.forEach(function(node) {
                    self.graphData.edges.forEach(function(edge) {
                        var neighbor = null;
                        if (edge.source.id === node.id && !visited[edge.target.id]) {
                            neighbor = edge.target;
                        } else if (edge.target.id === node.id && !visited[edge.source.id]) {
                            neighbor = edge.source;
                        }
                        
                        if (neighbor) {
                            visited[neighbor.id] = true;
                            nextRing.push(neighbor);
                        }
                    });
                });
                
                if (nextRing.length > 0) {
                    rings.push(nextRing);
                    currentRing = nextRing;
                } else {
                    break;
                }
            }
            
            // Position nodes in rings
            rings.forEach(function(ring, ringIndex) {
                if (ringIndex === 0) return;
                
                var radius = ringIndex * 100;
                var angleStep = (2 * Math.PI) / ring.length;
                
                ring.forEach(function(node, i) {
                    var angle = i * angleStep;
                    node.x = self.options.width / 2 + radius * Math.cos(angle);
                    node.y = self.options.height / 2 + radius * Math.sin(angle);
                    node.fixed = true;
                });
            });
            
            this.force.start();
            setTimeout(function() {
                self.graphData.nodes.forEach(function(node) {
                    node.fixed = false;
                });
            }, 2000);
        },
        
        /**
         * Apply hierarchical layout
         */
        applyHierarchicalLayout: function() {
            var self = this;
            
            // Create hierarchy based on node connections
            var levels = {};
            var maxLevel = 0;
            
            // Find root nodes (no incoming edges)
            this.graphData.nodes.forEach(function(node) {
                var hasIncoming = false;
                self.graphData.edges.forEach(function(edge) {
                    if (edge.target.id === node.id) {
                        hasIncoming = true;
                    }
                });
                
                if (!hasIncoming) {
                    levels[node.id] = 0;
                }
            });
            
            // Assign levels using BFS
            var changed = true;
            while (changed) {
                changed = false;
                
                this.graphData.edges.forEach(function(edge) {
                    if (levels[edge.source.id] !== undefined && levels[edge.target.id] === undefined) {
                        levels[edge.target.id] = levels[edge.source.id] + 1;
                        maxLevel = Math.max(maxLevel, levels[edge.target.id]);
                        changed = true;
                    }
                });
            }
            
            // Group nodes by level
            var nodesByLevel = {};
            this.graphData.nodes.forEach(function(node) {
                var level = levels[node.id] || maxLevel + 1;
                if (!nodesByLevel[level]) {
                    nodesByLevel[level] = [];
                }
                nodesByLevel[level].push(node);
            });
            
            // Position nodes
            var levelHeight = this.options.height / (Object.keys(nodesByLevel).length + 1);
            
            Object.keys(nodesByLevel).forEach(function(level) {
                var nodes = nodesByLevel[level];
                var nodeWidth = self.options.width / (nodes.length + 1);
                
                nodes.forEach(function(node, i) {
                    node.x = nodeWidth * (i + 1);
                    node.y = levelHeight * (parseInt(level) + 1);
                    node.fixed = true;
                });
            });
            
            this.force.start();
            setTimeout(function() {
                self.graphData.nodes.forEach(function(node) {
                    node.fixed = false;
                });
            }, 2000);
        },
        
        /**
         * Apply circular layout
         */
        applyCircularLayout: function() {
            var self = this;
            
            var radius = Math.min(this.options.width, this.options.height) / 2 - 50;
            var angleStep = (2 * Math.PI) / this.graphData.nodes.length;
            
            this.graphData.nodes.forEach(function(node, i) {
                var angle = i * angleStep;
                node.x = self.options.width / 2 + radius * Math.cos(angle);
                node.y = self.options.height / 2 + radius * Math.sin(angle);
                node.fixed = true;
            });
            
            this.force.start();
            setTimeout(function() {
                self.graphData.nodes.forEach(function(node) {
                    node.fixed = false;
                });
            }, 2000);
        },
        
        /**
         * Filter nodes by type
         */
        filterNodes: function() {
            var self = this;
            var checkedTypes = [];
            
            d3.selectAll('.type-filter input:checked').each(function() {
                checkedTypes.push(this.value);
            });
            
            this.nodes.style('display', function(d) {
                return checkedTypes.indexOf(d.type) >= 0 ? 'block' : 'none';
            });
            
            this.links.style('display', function(d) {
                return (checkedTypes.indexOf(d.source.type) >= 0 && 
                       checkedTypes.indexOf(d.target.type) >= 0) ? 'block' : 'none';
            });
        },
        
        /**
         * Search nodes
         */
        searchNodes: function() {
            var searchTerm = d3.select('.graph-search').property('value').toLowerCase();
            
            if (searchTerm === '') {
                this.nodes.style('opacity', 1);
                this.links.style('opacity', 0.6);
                return;
            }
            
            this.nodes.style('opacity', function(d) {
                return d.title.toLowerCase().indexOf(searchTerm) >= 0 ? 1 : 0.3;
            });
            
            this.links.style('opacity', function(d) {
                return (d.source.title.toLowerCase().indexOf(searchTerm) >= 0 ||
                       d.target.title.toLowerCase().indexOf(searchTerm) >= 0) ? 0.6 : 0.1;
            });
        }
    };

    // Initialize on document ready
    $(document).ready(function() {
        if ($('#knowledge-graph-container').length) {
            KnowledgeGraph.init('knowledge-graph-container');
        }
    });

})(jQuery);