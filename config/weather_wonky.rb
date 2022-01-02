#!/usr/bin/env ruby
require 'httparty'
require 'recursive-open-struct'
require 'json'
require 'date'

key = 'GetYourOwnDamnKey'
units = 'imperial'

# portsmouth nh
lat = 43.0718
lon = -70.7626

url = "https://api.openweathermap.org/data/2.5/onecall?lat=#{lat}&lon=#{lon}&appid=#{key}&exclude=minutely&units=#{units}"

resp = HTTParty.get(url)
w = JSON.parse(resp.body)
ws = RecursiveOpenStruct.new(w)
cur = ws.current

@icons = {
  :"01" => "\u2600".encode('utf-8'), # Sunny
  :"02" => "\u{1F324}".encode('utf-8'), # A little cloudy
  :"03" => "\u{1F325}".encode('utf-8'), # Pretty cloudy
  :"04" => "\u2601".encode('utf-8'), # Dark cloudy
  :"09" => "\u{1F327}".encode('utf-8'), # Rainy
  :"10" => "\u{1F327}".encode('utf-8'), # Rain and sun
  :"11" => "\u{1F329}".encode('utf-8'), # Lightning
  :"13" => "\u{1F328}".encode('utf-8'), # Snowy
  :"50" => "\u{1F32B}".encode('utf-8'), # Windy
}

def time(n)
  return Time.at(n).to_datetime.strftime('%r')
end

def sym(str)
  return "<span>#{ @icons[str.gsub(/[^0-9]/,'').to_sym]}</span>"
end

@str = "" 

def al(x=false, foo = false)
  if x
    @str += x
    if foo
      @str += foo
    end
  end
  @str += "\n"
end

sunrise = time(cur.sunrise)
sunset = time(cur.sunset)

al(cur.weather.map{|ww|
  x = RecursiveOpenStruct.new(ww);"#{sym(x.icon)} #{x.main} (#{x.description})"
}.join(" "))
al
al("Sunrise:"," #{sunrise}")
al("Sunset:"," #{sunset}")
al("Temp:"," #{cur.temp} F (feels like #{cur.feels_like} F)")
al("Humidity:"," #{cur.humidity}%")
al("Dew point:"," #{cur.dew_point}%")
al("Clouds:"," #{cur.clouds}%")
al("Visibility:"," #{cur.visibility}")
al("Wind speed:"," #{cur.wind_speed} mph")

puts @str
