

  // ------------------------------------------
  // Function to draw a chart
  // ------------------------------------------
  const activityChart = (graphX, graphY) => {

    $('#canvas-container').empty();
    $('#canvas-container').append('<canvas id="myChart"></canvas>');

    const ctx = document.getElementById('myChart').getContext('2d');
    console.log('graphX',graphX);
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: graphX,
            datasets: [{
                // label: 'Activity',
                backgroundColor: 'rgb(255, 99, 132)',
                borderColor: 'rgb(255, 99, 132)',
                data: graphY
            }]
        },
        options: {
          legend: {
            display: false
          },
          scales: {
            yAxes: [{
              ticks: {
                beginAtZero: true
              }
            }]
          }
        }
    });
  }

  // -------------------------------
  // Show allTime chart by default
  // -------------------------------
  let graphX = allTimeLabels;
  let graphY = allTimeData;
  activityChart(graphX, graphY);

  // -------------------------------------------------
  // jQuery on-click Event Listener for graph buttons
  // -------------------------------------------------
  $('.graph-buttons').on('click', (event) => { 
    console.log("Clicked on");
      console.log(event.target);
        console.log(event.target.id);

      // which button got clicked on  
      let button_id = event.target.id;

      let graphX;
      let graphY;

      if (button_id == "allTime") {
        console.log(button_id);
        graphX = allTimeLabels;
        graphY = allTimeData;
      }
      else if (button_id == "byWeek") {
        graphX = weekLabels;
        graphY = weekData;
      }
      else  {
        graphX = monthLabels;
        graphY = monthData;
      } 

    activityChart(graphX, graphY);
  });
