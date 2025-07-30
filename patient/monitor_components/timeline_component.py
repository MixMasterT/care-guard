def create_timeline_component(patient_data):
    """Create a D3-based timeline component for patient diagnosis history."""
    
    # Convert patient data to JSON for JavaScript
    import json
    timeline_data = []
    
    for diagnosis in patient_data.get('diagnoses', []):
        if diagnosis.get('onset_date'):
            # Filter out findings
            display = diagnosis.get('display', '')
            if 'finding' in display.lower():
                continue
                
            # Determine if this is a cardiac condition
            is_cardiac = any(keyword in display.lower() for keyword in [
                'postoperative', 'coronary', 'heart', 'cardiac', 'bypass', 'cabg', 
                'myocardial', 'infarction', 'angina', 'stenosis', 'valve', 'aortic',
                'percutaneous', 'intervention', 'pci'
            ])
            
            # Calculate end date
            onset_date = diagnosis.get('onset_date')
            abatement_date = diagnosis.get('abatement_date')
            
            # Handle procedures that might have different date fields
            if not onset_date and diagnosis.get('is_procedure'):
                # For procedures, try to get the performed date
                onset_date = diagnosis.get('recorded_date')
            
            if abatement_date:
                end_date = abatement_date
            elif is_cardiac:
                # Give cardiac conditions different durations
                from datetime import datetime, timedelta
                onset_dt = datetime.fromisoformat(onset_date.replace('Z', '+00:00'))
                if 'postoperative' in display.lower():
                    end_dt = onset_dt + timedelta(days=7)
                elif 'myocardial' in display.lower() or 'infarction' in display.lower():
                    end_dt = onset_dt + timedelta(days=7)
                elif 'coronary' in display.lower():
                    end_dt = onset_dt + timedelta(days=14)
                elif 'heart' in display.lower():
                    end_dt = onset_dt + timedelta(days=21)
                else:
                    end_dt = onset_dt + timedelta(days=30)
                end_date = end_dt.isoformat()
            else:
                # Use current date for active non-cardiac conditions
                from datetime import datetime
                end_date = datetime.now().isoformat()
            
            # Ensure minimum duration for visibility (at least 1 day)
            from datetime import datetime, timedelta
            start_dt = datetime.fromisoformat(onset_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            if start_dt == end_dt:
                # If start and end are the same, add minimum duration
                if is_cardiac:
                    end_dt = start_dt + timedelta(days=7)  # Cardiac conditions get 7 days minimum
                else:
                    end_dt = start_dt + timedelta(days=1)  # Others get 1 day minimum
                end_date = end_dt.isoformat()
            
            timeline_data.append({
                'id': diagnosis.get('id', ''),
                'display': display,
                'start': onset_date,
                'end': end_date,
                'status': diagnosis.get('clinical_status', 'unknown'),
                'is_cardiac': is_cardiac,
                'is_active': abatement_date is None
            })
    
    # Sort by start date (most recent first)
    timeline_data.sort(key=lambda x: x['start'], reverse=True)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Patient Diagnosis Timeline</title>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 10px;
                background-color: #f5f5f5;
                color: #333;
            }}
            
            .timeline-container {{
                position: relative;
                width: 100%;
                height: 700px;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .timeline-header {{
                padding: 15px;
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .timeline-title {{
                font-size: 18px;
                font-weight: bold;
                color: #495057;
            }}
            
            .slider-container {{
                display: flex;
                align-items: center;
                gap: 10px;
                flex: 1;
                margin-left: 20px;
            }}
            
            .slider-label {{
                font-size: 12px;
                color: #6c757d;
                white-space: nowrap;
            }}
            
            .time-slider {{
                flex: 1;
                height: 6px;
                border-radius: 3px;
                background: #e9ecef;
                outline: none;
                -webkit-appearance: none;
            }}
            
            .time-slider::-webkit-slider-thumb {{
                -webkit-appearance: none;
                appearance: none;
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: #007bff;
                cursor: pointer;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            
            .time-slider::-moz-range-thumb {{
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: #007bff;
                cursor: pointer;
                border: none;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            
            .timeline-chart {{
                position: relative;
                width: 100%;
                height: 400px;
                padding: 20px;
            }}
            
            .diagnosis-bar {{
                cursor: pointer;
                transition: opacity 0.2s;
            }}
            
            .diagnosis-bar:hover {{
                opacity: 0.8;
            }}
            
            .diagnosis-bar.cardiac {{
                fill: #dc3545;
            }}
            
            .diagnosis-bar.active {{
                fill: #fd7e14;
            }}
            
            .diagnosis-bar.resolved {{
                fill: #007bff;
            }}
            
            .diagnosis-bar.inactive {{
                fill: #6c757d;
            }}
            
            .diagnosis-label {{
                font-size: 11px;
                fill: #495057;
                text-anchor: middle;
            }}
            
            .axis text {{
                font-size: 10px;
                fill: #6c757d;
            }}
            
            .axis path,
            .axis line {{
                stroke: #dee2e6;
            }}
            
            .grid line {{
                stroke: #f8f9fa;
                stroke-width: 1;
            }}
            
            .tooltip {{
                position: absolute;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s;
            }}
        </style>
    </head>
    <body>
        <div class="timeline-container">
            <div class="timeline-header">
                <div class="timeline-title">Patient Diagnosis Timeline</div>
                <div class="slider-container">
                    <span class="slider-label">Full Timeline</span>
                    <input type="range" class="time-slider" id="timeSlider" min="0" max="100" value="0" step="5">
                    <span class="slider-label">Last 6 Months</span>
                </div>
            </div>
            <div class="timeline-chart">
                <svg id="timelineChart" width="100%" height="100%"></svg>
                <div class="tooltip" id="tooltip"></div>
            </div>
        </div>
        
        <script>
            // Timeline data from Python
            const timelineData = {json.dumps(timeline_data)};
            
            // Configuration
            const config = {{
                margin: {{ top: 20, right: 30, bottom: 60, left: 120 }},
                barHeight: 25,
                barSpacing: 5
            }};
            
            // State variables
            let timeWindowPercent = 0;
            let filteredData = [];
            
            // D3 elements
            let svg, chartGroup, xScale, yScale, xAxis, yAxis;
            let containerWidth, containerHeight;
            
            // Initialize the chart
            function initChart() {{
                const container = document.querySelector('.timeline-chart');
                containerWidth = container.clientWidth;
                containerHeight = container.clientHeight;
                
                // Clear existing chart
                d3.select('#timelineChart').selectAll('*').remove();
                
                // Create SVG
                svg = d3.select('#timelineChart')
                    .attr('width', containerWidth)
                    .attr('height', containerHeight);
                
                // Calculate chart dimensions
                const chartWidth = containerWidth - config.margin.left - config.margin.right;
                const chartHeight = containerHeight - config.margin.top - config.margin.bottom;
                
                // Create chart group (no clipping on main group to preserve axes)
                chartGroup = svg.append('g')
                    .attr('transform', `translate(${{config.margin.left}}, ${{config.margin.top}})`);
                
                // Add clipping path for bars only
                svg.append('defs')
                    .append('clipPath')
                    .attr('id', 'bars-clip')
                    .append('rect')
                    .attr('width', chartWidth)
                    .attr('height', chartHeight);
                
                // Create scales
                const timeExtent = d3.extent(timelineData, d => new Date(d.start));
                xScale = d3.scaleTime()
                    .domain(timeExtent)
                    .range([0, chartWidth]);
                
                yScale = d3.scaleBand()
                    .domain(timelineData.map(d => d.display))
                    .range([0, chartHeight])
                    .padding(0.1);
                
                // Create axes
                xAxis = d3.axisBottom(xScale)
                    .tickFormat(d3.timeFormat('%Y-%m-%d'));
                
                yAxis = d3.axisLeft(yScale);
                
                // Add grid
                chartGroup.append('g')
                    .attr('class', 'grid')
                    .attr('transform', `translate(0, ${{chartHeight}})`)
                    .call(d3.axisBottom(xScale)
                        .tickSize(-chartHeight)
                        .tickFormat('')
                    );
                
                // Add axes
                chartGroup.append('g')
                    .attr('class', 'axis')
                    .attr('transform', `translate(0, ${{chartHeight}})`)
                    .call(xAxis);
                
                chartGroup.append('g')
                    .attr('class', 'axis')
                    .call(yAxis);
                
                // Add title
                svg.append('text')
                    .attr('x', containerWidth / 2)
                    .attr('y', 15)
                    .attr('text-anchor', 'middle')
                    .style('font-size', '14px')
                    .style('font-weight', 'bold')
                    .text('Diagnosis Timeline');
            }}
            
            // Update the chart with filtered data
            function updateChart() {{
                const container = document.querySelector('.timeline-chart');
                containerWidth = container.clientWidth;
                containerHeight = container.clientHeight;
                
                const chartWidth = containerWidth - config.margin.left - config.margin.right;
                const chartHeight = containerHeight - config.margin.top - config.margin.bottom;
                
                // Keep all diagnoses visible - don't filter out any rows
                filteredData = timelineData;
                
                                // Calculate full extent from data
                const allDates = [];
                timelineData.forEach(d => {{
                    allDates.push(new Date(d.start));
                    allDates.push(new Date(d.end));
                }});
                const fullExtent = d3.extent(allDates);
                console.log('fullExtent before widening: ', fullExtent)
                // widen with one-month padding
                fullExtent[0].setMonth(fullExtent[0].getMonth() - 1)
                fullExtent[1].setMonth(fullExtent[1].getMonth() + 1)
                console.log('fullExtent after widening: ', fullExtent)


                if (timeWindowPercent > 0) {{
                  console.log('timeWindowPercent greater than 0: ', timeWindowPercent)
                  const slidabeTimeGapMs = (fullExtent[1].valueOf() - 180 * 24 * 60 * 60 * 1000) - fullExtent[0].valueOf()
                  console.log('slidabeTimeGapMs: ', slidabeTimeGapMs)
                  const startTimeOffset = slidabeTimeGapMs * (timeWindowPercent / 100)
                  console.log('startTimeOffset: ', startTimeOffset)
                  fullExtent[0] = new Date(fullExtent[0].valueOf() + startTimeOffset)
                }}
                console.log('fullExtent after window percent offset: ', fullExtent)
                
                xScale.domain(fullExtent).range([0, chartWidth]);
                
                yScale.domain(filteredData.map(d => d.display)).range([0, chartHeight]);
                
                // Update axes
                chartGroup.select('.axis').transition().duration(300).call(xAxis);
                chartGroup.selectAll('.axis').filter((d, i) => i === 1).transition().duration(300).call(yAxis);
                
                // Update grid
                chartGroup.select('.grid').transition().duration(300).call(
                    d3.axisBottom(xScale)
                        .tickSize(-chartHeight)
                        .tickFormat('')
                );
                
                // Update bars
                const bars = chartGroup.selectAll('.diagnosis-bar')
                    .data(filteredData, d => d.id);
                
                // Remove old bars
                bars.exit().remove();
                
                // Add new bars with clipping
                const barsEnter = bars.enter()
                    .append('rect')
                    .attr('class', 'diagnosis-bar')
                    .attr('clip-path', 'url(#bars-clip)')
                    .attr('y', d => yScale(d.display))
                    .attr('height', yScale.bandwidth())
                    .attr('x', d => {{
                        const startX = xScale(new Date(d.start));
                        return isNaN(startX) ? 0 : startX;
                    }})
                    .attr('width', d => {{
                        const startX = xScale(new Date(d.start));
                        const endX = xScale(new Date(d.end));
                        const width = endX - startX;
                        return isNaN(width) || width <= 0 ? 10 : Math.max(1, width); // Minimum 10px width
                    }})
                    .style('fill', d => getBarColor(d))
                    .on('mouseover', showTooltip)
                    .on('mouseout', hideTooltip);
                
                // Update existing bars
                bars.merge(barsEnter)
                    .transition()
                    .duration(300)
                    .attr('y', d => yScale(d.display))
                    .attr('height', yScale.bandwidth())
                    .attr('x', d => {{
                        const startX = xScale(new Date(d.start));
                        return isNaN(startX) ? 0 : startX;
                    }})
                    .attr('width', d => {{
                        const startX = xScale(new Date(d.start));
                        const endX = xScale(new Date(d.end));
                        const width = endX - startX;
                        return isNaN(width) || width <= 0 ? 10 : Math.max(1, width); // Minimum 10px width
                    }})
                    .style('fill', d => getBarColor(d));
            }}
            
            // Get bar color based on diagnosis type and status
            function getBarColor(diagnosis) {{
                if (diagnosis.is_cardiac) {{
                    return '#dc3545'; // Red for cardiac
                }} else if (diagnosis.status === 'active') {{
                    return '#fd7e14'; // Orange for active
                }} else if (diagnosis.status === 'resolved') {{
                    return '#007bff'; // Blue for resolved
                }} else {{
                    return '#6c757d'; // Gray for inactive
                }}
            }}
            
            // Show tooltip
            function showTooltip(event, d) {{
                const tooltip = d3.select('#tooltip');
                const formatDate = d3.timeFormat('%Y-%m-%d');
                
                tooltip.html(`
                    <strong>${{d.display}}</strong><br>
                    Start: ${{formatDate(new Date(d.start))}}<br>
                    End: ${{formatDate(new Date(d.end))}}<br>
                    Status: ${{d.status}}<br>
                    ${{d.is_cardiac ? 'Cardiac Condition' : 'Non-cardiac'}}
                `)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px')
                .style('opacity', 1);
            }}
            
            // Hide tooltip
            function hideTooltip() {{
                d3.select('#tooltip').style('opacity', 0);
            }}
            
            // Handle slider change
            function handleSliderChange() {{
                timeWindowPercent = parseInt(document.getElementById('timeSlider').value);
                updateChart();
            }}
            
            // Initialize everything
            function init() {{
                initChart();
                updateChart();
                
                // Add slider event listener
                document.getElementById('timeSlider').addEventListener('input', handleSliderChange);
                
                // Handle window resize
                window.addEventListener('resize', function() {{
                    setTimeout(() => {{
                        initChart();
                        updateChart();
                    }}, 100);
                }});
            }}
            
            // Start when page loads
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', init);
            }} else {{
                init();
            }}
        </script>
    </body>
    </html>
    """
    
    return html_content 