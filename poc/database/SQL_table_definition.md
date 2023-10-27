## Database table schema

## Devices table

CREATE TABLE public.devices (
  id INT8 NOT NULL DEFAULT unique_rowid(),
  hostname VARCHAR NULL,
  ip VARCHAR NULL,
  fingerprint_dhcp VARCHAR NULL,
  fingerbank_id INT8 NULL,
  fingerbank_name VARCHAR NULL,
  fingerbank_parents_id VARCHAR NULL,
  is_enabled BOOL NULL,
  category_id INT8 NULL,
  mac VARCHAR NULL,
  upnp_server_strings VARCHAR NULL,
  ssdp_url VARCHAR NULL,
  manufacturer VARCHAR NULL,
  modeldescription VARCHAR NULL,
  top5_dest_hosts_fqdn VARCHAR NULL,
  ports VARCHAR NULL,
  CONSTRAINT devices_pkey PRIMARY KEY (id ASC),
  CONSTRAINT devices_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id)
)


## Categories table

CREATE TABLE public.categories (
  id INT8 NOT NULL DEFAULT unique_rowid(),
  name VARCHAR NULL,
  classification_id VARCHAR NULL,
  fingerbank_ids INT8[] NULL,
  synonyms VARCHAR[] NULL,
  CONSTRAINT categories_pkey PRIMARY KEY (id ASC)
)


## Services table

CREATE TABLE public.services (
  id INT8 NOT NULL DEFAULT unique_rowid(),
  name VARCHAR NULL,
  direction VARCHAR NULL,
  tcp_ports VARCHAR NULL,
  udp_ports VARCHAR NULL,
  synonyms VARCHAR[] NULL,
  CONSTRAINT services_pkey PRIMARY KEY (id ASC)
)