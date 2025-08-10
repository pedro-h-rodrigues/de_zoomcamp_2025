Questions     [data-engineering-zoomcamp/cohorts/2025/01-docker-terraform](https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/cohorts/2025/01-docker-terraform/homework.md)


# Question 1. Understanding docker first run

my answer: pip 24.3.1

# Question 2. Understanding Docker networking and docker-compose

Hostname = db
port = 5432

# Question 3. Trip Segmentation Count

my answer: 104,802; 198,924; 109,603; 27,678; 35,189

# Question 4. Longest trip for each day

my answer: 2019-10-31

# Question 5. Three biggest pickup zones

my answer: "East Harlem North"
"East Harlem South"
"Morningside Heights"

```
with trips_with_index as (
select 
green_taxi_data.index,
green_taxi_data.lpep_pickup_datetime,
green_taxi_data.total_amount,
green_taxi_data."PULocationID",
zones."Borough",
zones."Zone"
from green_taxi_data
left join zones 
on green_taxi_data."PULocationID" = zones."LocationID"
where cast(lpep_pickup_datetime as Date) = '2019-10-18')

select trips_with_index."Borough", trips_with_index."Zone", sum(total_amount) from trips_with_index
group by trips_with_index."Borough", trips_with_index."Zone"
order by sum(total_amount) desc
limit 3;
```

# Question 6. Largest tip

my answer: JFK Airport

MY query:

```
with trips_with_index as (
select 
green_taxi_data.index,
green_taxi_data.lpep_pickup_datetime,
green_taxi_data.total_amount,
green_taxi_data.tip_amount,
green_taxi_data."PULocationID",
green_taxi_data."DOLocationID",
zones."Borough",
zones."Zone"
from green_taxi_data
left join zones 
on green_taxi_data."PULocationID" = zones."LocationID"
where cast(lpep_pickup_datetime as Date) >= '2019-10-01'
and cast(lpep_pickup_datetime as Date) < '2019-11-01'
and zones."Zone" = 'East Harlem North')

select trips_with_index.*,
zones."Borough" as DO_Borough,
zones."Zone" as DO_Zone
from trips_with_index
left join zones
on trips_with_index."DOLocationID" = zones."LocationID"
order by trips_with_index.tip_amount desc
```
