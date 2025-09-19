create table provider(
    provider_code varchar(255) primary key,
    name varchar(255),
    status int,
    city varchar(255)
);

create table detail(
    detail_code varchar(255) primary key ,
    name varchar(255),
    color varchar(255),
    size int,
    city varchar(255)
);

create table project(
    project_code varchar(255) primary key ,
    name varchar(255),
    city varchar(255)
);

create table number_of_details(
    provider_code varchar(255) references provider(provider_code),
    detail_code varchar(255) references detail(detail_code),
    project_code varchar(255) references project(project_code),
    number int
);

insert into provider (provider_code, name, status, city)
VALUES ('P1', 'Petrov', 20, 'Moscow'),
       ('P2', 'Sinicin', 10, 'Tallin'),
       ('P3', 'Federov', 30, 'Tallin'),
       ('P4', 'Chaianov', 20, 'Minsk'),
       ('P5', 'Krykov', 30, 'Kiev');

insert into detail (detail_code, name, color, size, city)
VALUES ('D1', 'Bolt', 'Red', 12, 'Moscow'),
       ('D2', 'Gaika', 'Green', 17, 'Minsk'),
       ('D3', 'Disk', 'Black', 17, 'Vilnus'),
       ('D4', 'Disk', 'Black', 14, 'Moscow'),
       ('D5', 'Korpus', 'Red', 12, 'Minsk'),
       ('D6', 'Krishki', 'Red', 19, 'Moscow');

insert into project (project_code, name, city)
VALUES ('PR1', 'IPR1', 'Minsk'),
       ('PR2', 'IPR2', 'Tallin'),
       ('PR3', 'IPR3', 'Pskov'),
       ('PR4', 'IPR4', 'Pskov'),
       ('PR5', 'IPR4', 'Moscow'),
       ('PR6', 'IPR6', 'Saratov'),
       ('PR7', 'IPR7', 'Moscow');

insert into number_of_details (provider_code, detail_code, project_code, number)
VALUES ('P1', 'D1', 'PR1', 200),
       ('P1', 'D1', 'PR2', 700),
       ('P2', 'D3', 'PR1', 400),
       ('P2', 'D2', 'PR2', 200),
       ('P2', 'D3', 'PR3', 200),
       ('P2', 'D3', 'PR4', 500),
       ('P2', 'D3', 'PR5', 600),
       ('P2', 'D3', 'PR6', 400),
       ('P2', 'D3', 'PR7', 800),
       ('P2', 'D5', 'PR2', 100),
       ('P3', 'D3', 'PR1', 200),
       ('P3', 'D4', 'PR2', 500),
       ('P4', 'D6', 'PR3', 300),
       ('P4', 'D6', 'PR7', 300),
       ('P5', 'D2', 'PR2', 200),
       ('P5', 'D2', 'PR4', 100),
       ('P5', 'D5', 'PR5', 500),
       ('P5', 'D5', 'PR7', 100),
       ('P5', 'D6', 'PR2', 200),
       ('P5', 'D1', 'PR2', 100),
       ('P5', 'D3', 'PR4', 200),
       ('P5', 'D4', 'PR4', 800),
       ('P5', 'D5', 'PR4', 400),
       ('P5', 'D6', 'PR4', 500);


-- 20. Получить цвета деталей, поставляемых поставщиком П1.
SELECT DISTINCT d.color FROM detail d
JOIN number_of_details ON d.detail_code = number_of_details.detail_code
WHERE number_of_details.provider_code = 'P1';

--24. Получить номера поставщиков со статусом, меньшим чем у поставщика П1.
SELECT provider.provider_code FROM provider
WHERE provider.status < (SELECT status FROM provider WHERE provider.provider_code = 'P1'); 

-- 17. Для каждой детали, поставляемой для проекта, получить номер детали, номер проекта и соответствующее общее количество.
SELECT p.project_code, nd.detail_code, SUM(nd.number) AS total_number FROM number_of_details AS nd
JOIN project AS p ON nd.project_code = p.project_code
GROUP BY p.project_code, nd.detail_code;

-- 32. Получить номера проектов, обеспечиваемых по крайней мере всеми деталями поставщика П1.
SELECT DISTINCT nd.project_code FROM number_of_details AS nd
WHERE nd.detail_code IN (SELECT detail_code FROM number_of_details WHERE provider_code = 'P1')
GROUP BY nd.project_code
HAVING COUNT(DISTINCT nd.detail_code) = (SELECT COUNT(DISTINCT detail_code) FROM number_of_details WHERE provider_code = 'P1');

-- 10. Получить номера деталей, поставляемых поставщиком в Лондоне для проекта в Лондоне.
SELECT DISTINCT detail_code FROM  provider AS pr
JOIN number_of_details ON pr.provider_code = number_of_details.provider_code
JOIN project on number_of_details.project_code = project.project_code
WHERE pr.city = 'London' and project.city = 'London';

-- 8.  Получить все такие тройки "номера-поставщиков номера-деталей номера-проектов", для которых никакие из двух выводимых поставщиков, деталей и проектов не размещены в одном городе. 
SELECT provider.provider_code, detail.detail_code, project.project_code FROM provider
JOIN number_of_details  on provider.provider_code = number_of_details.provider_code
JOIN project on number_of_details.project_code = project.project_code
JOIN detail on number_of_details.detail_code = detail.detail_code
WHERE provider.city <> detail.city AND detail.city <> project.city AND provider.city <> project.city;

-- 11. Получить все пары названий городов, для которых поставщик из первого города обеспечивает проект во втором городе.
SELECT DISTINCT project.city, provider.city FROM provider
JOIN number_of_details on provider.provider_code = number_of_details.provider_code
JOIN project on number_of_details.project_code = project.project_code;

-- 7.  Получить все такие тройки "номера поставщиковb номера деталей номера проектов", для которых выводимые поставщик, деталь и проект не размещены в одном городе.
SELECT provider.provider_code, detail.detail_code, project.project_code FROM provider
JOIN number_of_details  on provider.provider_code = number_of_details.provider_code
JOIN project on number_of_details.project_code = project.project_code
JOIN detail on number_of_details.detail_code = detail.detail_code
WHERE NOT  ( detail.city = project.city AND provider.city = project.city);

-- 36. Получить все пары номеров поставщиков, скажем, Пx и Пy, такие, что оба эти поставщика поставляют в точности одно и то же множество деталей.
SELECT p1.provider_code AS provider1, p2.provider_code AS provider2 FROM provider p1
JOIN provider p2 ON p1.provider_code < p2.provider_code
WHERE NOT EXISTS (
    SELECT detail_code FROM number_of_details WHERE provider_code = p1.provider_code
    EXCEPT
    SELECT detail_code FROM number_of_details WHERE provider_code = p2.provider_code
)
AND NOT EXISTS (
    SELECT detail_code FROM number_of_details WHERE provider_code = p2.provider_code
    EXCEPT
    SELECT detail_code FROM number_of_details WHERE provider_code = p1.provider_code
);

-- 26. Получить номера проектов, для которых среднее количество поставляемых деталей Д1 больше, чем наибольшее количество любых деталей, поставляемых для проекта ПР1.
SELECT project_code FROM number_of_details
WHERE detail_code = 'D1'
GROUP BY project_code
HAVING AVG(number) > (SELECT MAX(number) FROM number_of_details WHERE project_code = 'PR1');


-- SELECT
--     user_id,
--     COUNT(*) AS total_messages,
--     COUNT(DISTINCT receiver_id) AS unique_con,
--     MAX(msg_count_in_window) AS max_msg_in_5_sec,
--     AVG(LENGTH(message_text)) AS avg_message_length,
--     COUNT(DISTINCT receiver_id) * 1.0 / NULLIF(COUNT(*), 0) AS diversity_ratio,
-- FROM (
--     SELECT
--         *,
--         COUNT(*) OVER (PARTITION BY user_id ORDER BY timestamp ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS msg_count_in_window
--     FROM messages
-- ) AS subquery
-- GROUP BY user_id;
   