"use client";

import { ColumnDef } from "@tanstack/react-table";

import { Badge } from "@/components/ui/badge";
import { SquareArrowOutUpRight } from "lucide-react";
import { labels, statuses } from "@/lib/data/data";
// import { priorities } from "@/lib/data/data"
import { Task } from "@/lib/data/schema";
import { DataTableColumnHeader } from "./data-table-column-header";
import { DataTableRowActions } from "./data-table-row-actions";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export const columns: ColumnDef<Task>[] = [
  // {
  //   id: "select",
  //   header: ({ table }) => (
  //     <Checkbox
  //       checked={
  //         table.getIsAllPageRowsSelected() ||
  //         (table.getIsSomePageRowsSelected() && "indeterminate")
  //       }
  //       onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
  //       aria-label="Select all"
  //       className="translate-y-[2px]"
  //     />
  //   ),
  //   cell: ({ row }) => (
  //     <Checkbox
  //       checked={row.getIsSelected()}
  //       onCheckedChange={(value) => row.toggleSelected(!!value)}
  //       aria-label="Select row"
  //       className="translate-y-[2px]"
  //     />
  //   ),
  //   enableSorting: false,
  //   enableHiding: false,
  // },
  // {
  //   accessorKey: "id",
  //   header: ({ column }) => (
  //     <DataTableColumnHeader column={column} title="Task" />
  //   ),
  //   cell: ({ row }) => <div className="w-[80px]">{row.getValue("id")}</div>,
  //   enableSorting: false,
  //   enableHiding: false,
  // },
  {
    accessorKey: "title",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Title" />
    ),
    cell: ({ row }) => {
      const label = row.original.label;

      return (
        <div className="flex space-x-2">
          {label && <Badge variant="outline">{label}</Badge>}
          <span className="max-w-[400px] truncate font-medium">
            {row.getValue("title")}
          </span>
        </div>
      );
    },
  },
  {
    accessorKey: "status",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Status" />
    ),
    cell: ({ row }) => {
      const status = statuses.find(
        (status) => status.value === row.getValue("status"),
      );

      if (!status) {
        return null;
      }

      return (
        <div className="flex w-[100px] items-center">
          {status.icon && (
            <status.icon className="mr-2 h-4 w-4 text-muted-foreground" />
          )}
          <span>{status.label}</span>
        </div>
      );
    },
    filterFn: (row, id, value) => {
      return value.includes(row.getValue(id));
    },
  },
  {
    accessorKey: "ttl",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Time to Expiry" />
    ),
    cell: ({ row }) => {
      const ttl = Number(row.getValue("ttl"));

      if (isNaN(ttl)) {
        // Handle invalid number
        return null;
      }

      let formattedTtl = "";

      if (ttl === -1) {
        formattedTtl = "None";
      } else if (ttl === 0) {
        formattedTtl = "Expired";
      } else if (ttl < 60) {
        formattedTtl = `${ttl} minutes`;
      } else {
        const days = Math.floor(ttl / (24 * 60));
        const hours = Math.floor((ttl % (24 * 60)) / 60);
        const minutes = ttl % 60;

        formattedTtl = [
          days > 0 ? `${days} day${days > 1 ? "s" : ""}` : null,
          hours > 0 ? `${hours} hour${hours > 1 ? "s" : ""}` : null,
          minutes > 0 ? `${minutes} minute${minutes > 1 ? "s" : ""}` : null,
        ]
          .filter(Boolean)
          .join(", ");
      }

      return <div className="flex items-center">{formattedTtl}</div>;
    },
    filterFn: (row, id, value) => {
      return value.includes(row.getValue(id));
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const url = `/jobs/${row.original.title}-${row.original.label}-${row.original.id}`;

      return (
        <Button variant={"link"} size={"icon"} className="h-4 w-4" asChild>
          <Link href={url}>
            <SquareArrowOutUpRight
              strokeWidth={2}
              className="text-blue-600 hover:text-blue-800 h-4 w-4"
            />
          </Link>
        </Button>
      );
    },
  },
];
