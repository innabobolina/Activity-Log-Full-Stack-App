
  $("#sms-text").hide();

  let sms_flag = 0
  

  $('#sms-click').on('click', () => {

    if (sms_flag == 0) {
      
      $.get('/send_sms', (res) => {

        console.log("sms res:", res); 
        $('#sms-text').html(`SMS text: ${res.mytext}`);
        $('#sms-text').show();
        $('#sms-click').html("SMS has been sent!");
       
        sms_flag = 1 
      });
    }

    else {
        $('#sms-click').html("Click to send an SMS");
        $('#sms-text').hide();

        sms_flag = 0
    }
  });


  $("#forecast").hide();

  let forecast_flag = 0
  
  $('#forecast-click').on('click', () => {

    if (forecast_flag == 0) {
        $('#forecast').show();
        $('#forecast-click').html("Click to hide forecast");

        forecast_flag = 1 
    }

    else {
        $('#forecast-click').html("Click for weather forecast for the next 7 days");
        $('#forecast').hide();

        forecast_flag = 0
    }
  });
