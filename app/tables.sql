create database collection_manager;
\connect collection_manager

create table collection (
	collection_id serial primary key,
	collection_name text,
	collection_doi text,
	collection_slug text not null unique
);

comment on column collection.collection_slug is 'The unique identifier used by PRISM APIs to refer to the collection, [-_a-zA-Z0-9]';

create table data_manager (
	data_manager_id serial primary key,
	data_manager_name text not null unique
);

create table file_type (
	file_type_id serial primary key,
	mime_type text not null unique
);

create table file_type_group (
	file_type_id integer not null references file_type,
	file_type_group_name text not null unique,
	primary key (file_type_id, file_type_group_name)
);

create table file (
	file_id serial primary key,
	data_manager_id integer not null references data_manager,
	file_type_id integer not null references file_type,
	external_id text not null
);

create table version (
	version_id serial primary key,
	collection_id integer not null references collection,
	name text,
	description text,
	created_on timestamp not null default now()
);

create table version_file (
	version_id integer references version,
	file_id integer references file,
	primary key (version_id, file_id)
);

create table collection_info (
	collection_id integer references collection not null,
	description text
);
