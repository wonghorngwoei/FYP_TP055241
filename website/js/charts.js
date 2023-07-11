// custom.js

$(document).ready(function() {
    // Mock data for chart and statistics
    var asthmaCount = 50;
    var diabetesCount = 75;
    var strokeCount = 30;
    var totalUsersCount = 100;
    var totalPredictionsCount = asthmaCount + diabetesCount + strokeCount;
    var recentUsersList = ["User A", "User B", "User C"];
  
    // Update the chart and statistics values
    updateChart();
    updateStatistics();
  
    // Function to update the chart
    function updateChart() {
      var chartData = {
        labels: ["Asthma", "Diabetes", "Stroke"],
        datasets: [{
          label: "Predictions Count",
          data: [asthmaCount, diabetesCount, strokeCount],
          backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56"]
        }]
      };
  
      var chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true
          }
        }
      };
  
      var predictionsChart = document.getElementById("predictionsChart").getContext("2d");
      new Chart(predictionsChart, {
        type: "bar",
        data: chartData,
        options: chartOptions
      });
    }
  
    // Function to update the statistics
    function updateStatistics() {
      $("#asthmaCount").text(asthmaCount);
      $("#diabetesCount").text(diabetesCount);
      $("#strokeCount").text(strokeCount);
      $("#totalUsersCount").text(totalUsersCount);
      $("#totalPredictionsCount").text(totalPredictionsCount);
  
      var recentUsersHtml = "";
      recentUsersList.forEach(function(user) {
        recentUsersHtml += "<li>" + user + "</li>";
      });
      $("#recentUsersList").html(recentUsersHtml);
    }
  });
  