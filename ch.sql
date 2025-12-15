CREATE TABLE IF NOT EXISTS tpch.region
(
    r_regionkey Int32,
    r_name      String,
    r_comment   String
)
ENGINE = MergeTree
ORDER BY r_regionkey;

CREATE TABLE IF NOT EXISTS tpch.nation
(
    n_nationkey Int32,
    n_name      String,
    n_regionkey Int32,
    n_comment   String
)
ENGINE = MergeTree
ORDER BY n_nationkey;

CREATE TABLE IF NOT EXISTS tpch.supplier
(
    s_suppkey   Int32,
    s_name      String,
    s_address   String,
    s_nationkey Int32,
    s_phone     String,
    s_acctbal   Float64,
    s_comment   String
)
ENGINE = MergeTree
ORDER BY s_suppkey;

CREATE TABLE IF NOT EXISTS tpch.customer
(
    c_custkey    Int32,
    c_name       String,
    c_address    String,
    c_nationkey  Int32,
    c_phone      String,
    c_acctbal    Float64,
    c_mktsegment String,
    c_comment    String
)
ENGINE = MergeTree
ORDER BY c_custkey;

CREATE TABLE IF NOT EXISTS tpch.part
(
    p_partkey     Int32,
    p_name        String,
    p_mfgr        String,
    p_brand       String,
    p_type        String,
    p_size        Int32,
    p_container   String,
    p_retailprice Float64,
    p_comment     String
)
ENGINE = MergeTree
ORDER BY p_partkey;

CREATE TABLE IF NOT EXISTS tpch.partsupp
(
    ps_partkey    Int32,
    ps_suppkey    Int32,
    ps_availqty   Int32,
    ps_supplycost Float64,
    ps_comment    String
)
ENGINE = MergeTree
ORDER BY (ps_partkey, ps_suppkey);

CREATE TABLE IF NOT EXISTS tpch.orders
(
    o_orderkey      Int32,
    o_custkey       Int32,
    o_orderstatus   String,
    o_totalprice    Float64,
    o_orderdate     Date,
    o_orderpriority String,
    o_clerk         String,
    o_shippriority  Int32,
    o_comment       String
)
ENGINE = MergeTree
ORDER BY o_orderkey;

CREATE TABLE IF NOT EXISTS tpch.lineitem
(
    l_orderkey      Int32,
    l_partkey       Int32,
    l_suppkey       Int32,
    l_linenumber    Int32,
    l_quantity      Float64,
    l_extendedprice Float64,
    l_discount      Float64,
    l_tax           Float64,
    l_returnflag    String,
    l_linestatus    String,
    l_shipdate      Date,
    l_commitdate    Date,
    l_receiptdate   Date,
    l_shipinstruct  String,
    l_shipmode      String,
    l_comment       String
)
ENGINE = MergeTree
ORDER BY (l_orderkey, l_linenumber);
