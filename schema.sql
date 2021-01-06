drop table if exists Regions       cascade;
drop table if exists Businesses    cascade;
drop table if exists Users         cascade;
drop table if exists Own_Accounts  cascade;
drop table if exists Friends_of    cascade;
drop table if exists Records       cascade;
drop table if exists Stocks        cascade;
drop table if exists Exchanges     cascade;
drop table if exists Traded_on     cascade;

create table Regions (
    name         varchar(128)     primary key,
    population   decimal,
    GDP          decimal
);

create table Businesses (
    name         varchar(128)     primary key,
    year         integer          not null
);

create table Users (
    id           serial           primary key,
    name         varchar(128)     not null,
    password	 varchar(128) 	  not null,
    workplace    varchar(128),
    region_in    varchar(128),
    foreign key  (workplace)      references Businesses(name),
    foreign key  (region_in)      references Regions(name)
);

create table Own_Accounts (
    id             serial         unique not null,
    uid            integer        not null,
    primary key    (id, uid),
    balance        decimal,
    foreign key    (uid)          references Users(id) on delete cascade
);

create table Friends_Of (
    uid            integer        not null,
    fid            integer        not null,
    fname          varchar(128)   not null,
    primary key    (uid, fid),
    foreign key    (uid)          references Users(id) on delete cascade
);


create table Stocks (
    ticker         varchar(6)     primary key,
    name           varchar(128)   not null,
    business       varchar(128),
    foreign key    (business)     references Businesses(name)
);

create table Records (
    id             serial         primary key,
    tTime          timestamp without time zone default (now() at time zone 'utc'),
    buysell        boolean        not null,
    cost           decimal        not null,
    platform       varchar(128),
    nShares        integer,
    ticker         varchar(6)     not null,
    uid            integer        not null,
    foreign key    (ticker)       references Stocks(ticker),
    foreign key    (uid)          references Users(id) on delete cascade
);

create table Exchanges (
    shortname      varchar(8)    primary key,
    name           varchar(128)  unique not null,
    region         varchar(128),
    foreign key    (region)      references Regions(name)
);

create table Traded_On (
    ename          varchar(8)    not null,
    sTicker        varchar(6)    not null,
    primary key    (ename, sTicker),
    foreign key    (ename)       references Exchanges(shortname),
    foreign key    (sTicker)     references Stocks(Ticker)
);

