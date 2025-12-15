CREATE FOREIGN TABLE clickhouse.customer (
  c_custkey     integer,
  c_name        text,
  c_address     text,
  c_nationkey   integer,
  c_phone       text,
  c_acctbal     double precision,
  c_mktsegment  text,
  c_comment     text
)
SERVER ch1
OPTIONS (database 'tpch', table_name 'customer');

CREATE FOREIGN TABLE clickhouse.orders (
  o_orderkey      integer,
  o_custkey       integer,
  o_orderstatus   text,
  o_totalprice    double precision,
  o_orderdate     date,
  o_orderpriority text,
  o_clerk         text,
  o_shippriority  integer,
  o_comment       text
)
SERVER ch1
OPTIONS (database 'tpch', table_name 'orders');

CREATE FOREIGN TABLE clickhouse.lineitem (
  l_orderkey      integer,
  l_partkey       integer,
  l_suppkey       integer,
  l_linenumber    integer,
  l_quantity      double precision,
  l_extendedprice double precision,
  l_discount      double precision,
  l_tax           double precision,
  l_returnflag    text,
  l_linestatus    text,
  l_shipdate      date,
  l_commitdate    date,
  l_receiptdate   date,
  l_shipinstruct  text,
  l_shipmode      text,
  l_comment       text
)
SERVER ch1
OPTIONS (database 'tpch', table_name 'lineitem');

CREATE FOREIGN TABLE clickhouse.part (
  p_partkey     integer,
  p_name        text,
  p_mfgr        text,
  p_brand       text,
  p_type        text,
  p_size        integer,
  p_container   text,
  p_retailprice double precision,
  p_comment     text
)
SERVER ch1
OPTIONS (database 'tpch', table_name 'part');

CREATE FOREIGN TABLE clickhouse.supplier (
  s_suppkey   integer,
  s_name      text,
  s_address   text,
  s_nationkey integer,
  s_phone     text,
  s_acctbal   double precision,
  s_comment   text
)
SERVER ch1
OPTIONS (database 'tpch', table_name 'supplier');

CREATE FOREIGN TABLE clickhouse.partsupp (
  ps_partkey    integer,
  ps_suppkey    integer,
  ps_availqty   integer,
  ps_supplycost double precision,
  ps_comment    text
)
SERVER ch1
OPTIONS (database 'tpch', table_name 'partsupp');

CREATE FOREIGN TABLE clickhouse.nation (
  n_nationkey integer,
  n_name      text,
  n_regionkey integer,
  n_comment   text
)
SERVER ch1
OPTIONS (database 'tpch', table_name 'nation');

CREATE FOREIGN TABLE clickhouse.region (
  r_regionkey integer,
  r_name      text,
  r_comment   text
)
SERVER ch1
OPTIONS (database 'tpch', table_name 'region');
