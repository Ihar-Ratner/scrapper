--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Ubuntu 14.18-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.18 (Ubuntu 14.18-0ubuntu0.22.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: articles; Type: TABLE; Schema: public; Owner: bot_user
--

CREATE TABLE public.articles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    articule character varying(20) NOT NULL,
    added_at timestamp without time zone
);


ALTER TABLE public.articles OWNER TO bot_user;

--
-- Name: articles_id_seq; Type: SEQUENCE; Schema: public; Owner: bot_user
--

CREATE SEQUENCE public.articles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.articles_id_seq OWNER TO bot_user;

--
-- Name: articles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bot_user
--

ALTER SEQUENCE public.articles_id_seq OWNED BY public.articles.id;


--
-- Name: cache_entries; Type: TABLE; Schema: public; Owner: bot_user
--

CREATE TABLE public.cache_entries (
    id integer NOT NULL,
    articule character varying(20) NOT NULL,
    product_name text NOT NULL,
    final_price character varying(50) NOT NULL,
    cached_at timestamp without time zone,
    expires_at timestamp without time zone NOT NULL
);


ALTER TABLE public.cache_entries OWNER TO bot_user;

--
-- Name: cache_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: bot_user
--

CREATE SEQUENCE public.cache_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cache_entries_id_seq OWNER TO bot_user;

--
-- Name: cache_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bot_user
--

ALTER SEQUENCE public.cache_entries_id_seq OWNED BY public.cache_entries.id;


--
-- Name: error_logs; Type: TABLE; Schema: public; Owner: bot_user
--

CREATE TABLE public.error_logs (
    id integer NOT NULL,
    user_id integer,
    articule character varying(20),
    error_type character varying(50) NOT NULL,
    error_message text NOT NULL,
    context text,
    created_at timestamp without time zone
);


ALTER TABLE public.error_logs OWNER TO bot_user;

--
-- Name: error_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: bot_user
--

CREATE SEQUENCE public.error_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.error_logs_id_seq OWNER TO bot_user;

--
-- Name: error_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bot_user
--

ALTER SEQUENCE public.error_logs_id_seq OWNED BY public.error_logs.id;


--
-- Name: product_prices; Type: TABLE; Schema: public; Owner: bot_user
--

CREATE TABLE public.product_prices (
    id integer NOT NULL,
    articule character varying(20) NOT NULL,
    product_name text NOT NULL,
    final_price character varying(50) NOT NULL,
    price_float double precision,
    is_sold_out boolean,
    user_id integer NOT NULL,
    scraped_at timestamp without time zone
);


ALTER TABLE public.product_prices OWNER TO bot_user;

--
-- Name: product_prices_id_seq; Type: SEQUENCE; Schema: public; Owner: bot_user
--

CREATE SEQUENCE public.product_prices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.product_prices_id_seq OWNER TO bot_user;

--
-- Name: product_prices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bot_user
--

ALTER SEQUENCE public.product_prices_id_seq OWNED BY public.product_prices.id;


--
-- Name: subscriptions; Type: TABLE; Schema: public; Owner: bot_user
--

CREATE TABLE public.subscriptions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    interval_seconds integer,
    is_active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.subscriptions OWNER TO bot_user;

--
-- Name: subscriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: bot_user
--

CREATE SEQUENCE public.subscriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.subscriptions_id_seq OWNER TO bot_user;

--
-- Name: subscriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bot_user
--

ALTER SEQUENCE public.subscriptions_id_seq OWNED BY public.subscriptions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: bot_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    telegram_id integer NOT NULL,
    username character varying(100),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO bot_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: bot_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO bot_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: bot_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: articles id; Type: DEFAULT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.articles ALTER COLUMN id SET DEFAULT nextval('public.articles_id_seq'::regclass);


--
-- Name: cache_entries id; Type: DEFAULT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.cache_entries ALTER COLUMN id SET DEFAULT nextval('public.cache_entries_id_seq'::regclass);


--
-- Name: error_logs id; Type: DEFAULT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.error_logs ALTER COLUMN id SET DEFAULT nextval('public.error_logs_id_seq'::regclass);


--
-- Name: product_prices id; Type: DEFAULT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.product_prices ALTER COLUMN id SET DEFAULT nextval('public.product_prices_id_seq'::regclass);


--
-- Name: subscriptions id; Type: DEFAULT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.subscriptions ALTER COLUMN id SET DEFAULT nextval('public.subscriptions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: articles; Type: TABLE DATA; Schema: public; Owner: bot_user
--

COPY public.articles (id, user_id, articule, added_at) FROM stdin;
9	364418135	224899085	2025-08-13 07:35:38.372118
10	364418135	317200674	2025-08-13 07:59:00.922087
\.


--
-- Data for Name: cache_entries; Type: TABLE DATA; Schema: public; Owner: bot_user
--

COPY public.cache_entries (id, articule, product_name, final_price, cached_at, expires_at) FROM stdin;
\.


--
-- Data for Name: error_logs; Type: TABLE DATA; Schema: public; Owner: bot_user
--

COPY public.error_logs (id, user_id, articule, error_type, error_message, context, created_at) FROM stdin;
\.


--
-- Data for Name: product_prices; Type: TABLE DATA; Schema: public; Owner: bot_user
--

COPY public.product_prices (id, articule, product_name, final_price, price_float, is_sold_out, user_id, scraped_at) FROM stdin;
176	224899085	Шлепанцы уличные домашние пляжные	34,44 р.	34.44	f	364418135	2025-08-13 07:35:47.499871
178	224899085	Шлепанцы уличные домашние пляжные	34,44 р.	34.44	f	364418135	2025-08-13 07:36:55.073604
180	224899085	Шлепанцы уличные домашние пляжные	34,44 р.	34.44	f	364418135	2025-08-13 07:45:26.824338
182	224899085	Шлепанцы уличные домашние пляжные	35,14 р.	35.14	f	364418135	2025-08-13 07:50:58.688008
184	224899085	Шлепанцы уличные домашние пляжные	35,14 р.	35.14	f	364418135	2025-08-13 07:51:19.052639
186	224899085	Шлепанцы уличные домашние пляжные	35,14 р.	35.14	f	364418135	2025-08-13 07:52:27.646319
188	224899085	Шлепанцы уличные домашние пляжные	35,14 р.	35.14	f	364418135	2025-08-13 07:53:27.63157
\.


--
-- Data for Name: subscriptions; Type: TABLE DATA; Schema: public; Owner: bot_user
--

COPY public.subscriptions (id, user_id, interval_seconds, is_active, created_at, updated_at) FROM stdin;
1	364418135	60	f	2025-08-05 13:50:01.842222	2025-08-13 07:53:35.103238
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: bot_user
--

COPY public.users (id, telegram_id, username, created_at, updated_at) FROM stdin;
1	364418135	igorat93	2025-08-05 13:34:39.834373	2025-08-05 13:34:39.834385
\.


--
-- Name: articles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: bot_user
--

SELECT pg_catalog.setval('public.articles_id_seq', 10, true);


--
-- Name: cache_entries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: bot_user
--

SELECT pg_catalog.setval('public.cache_entries_id_seq', 1, false);


--
-- Name: error_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: bot_user
--

SELECT pg_catalog.setval('public.error_logs_id_seq', 1, false);


--
-- Name: product_prices_id_seq; Type: SEQUENCE SET; Schema: public; Owner: bot_user
--

SELECT pg_catalog.setval('public.product_prices_id_seq', 188, true);


--
-- Name: subscriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: bot_user
--

SELECT pg_catalog.setval('public.subscriptions_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: bot_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: articles articles_pkey; Type: CONSTRAINT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_pkey PRIMARY KEY (id);


--
-- Name: cache_entries cache_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.cache_entries
    ADD CONSTRAINT cache_entries_pkey PRIMARY KEY (id);


--
-- Name: error_logs error_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.error_logs
    ADD CONSTRAINT error_logs_pkey PRIMARY KEY (id);


--
-- Name: product_prices product_prices_pkey; Type: CONSTRAINT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.product_prices
    ADD CONSTRAINT product_prices_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_pkey PRIMARY KEY (id);


--
-- Name: subscriptions subscriptions_user_id_key; Type: CONSTRAINT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.subscriptions
    ADD CONSTRAINT subscriptions_user_id_key UNIQUE (user_id);


--
-- Name: articles uq_user_article; Type: CONSTRAINT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT uq_user_article UNIQUE (user_id, articule);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_telegram_id_key; Type: CONSTRAINT; Schema: public; Owner: bot_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_telegram_id_key UNIQUE (telegram_id);


--
-- Name: ix_cache_entries_articule; Type: INDEX; Schema: public; Owner: bot_user
--

CREATE UNIQUE INDEX ix_cache_entries_articule ON public.cache_entries USING btree (articule);


--
-- Name: ix_cache_entries_expires_at; Type: INDEX; Schema: public; Owner: bot_user
--

CREATE INDEX ix_cache_entries_expires_at ON public.cache_entries USING btree (expires_at);


--
-- Name: ix_error_logs_created_at; Type: INDEX; Schema: public; Owner: bot_user
--

CREATE INDEX ix_error_logs_created_at ON public.error_logs USING btree (created_at);


--
-- Name: ix_product_prices_articule; Type: INDEX; Schema: public; Owner: bot_user
--

CREATE INDEX ix_product_prices_articule ON public.product_prices USING btree (articule);


--
-- Name: ix_product_prices_scraped_at; Type: INDEX; Schema: public; Owner: bot_user
--

CREATE INDEX ix_product_prices_scraped_at ON public.product_prices USING btree (scraped_at);


--
-- PostgreSQL database dump complete
--

