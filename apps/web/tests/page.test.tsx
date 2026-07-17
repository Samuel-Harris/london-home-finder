import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import Home from "../src/app/page";

describe("Home", () => {
  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_URL;
  });

  it("introduces the local home research workspace", () => {
    render(<Home />);

    expect(
      screen.getByRole("heading", {
        name: "Find a London home with the evidence in one place.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/http:\/\/localhost:8000/)).toBeInTheDocument();
  });

  it("shows the explicitly configured API endpoint", () => {
    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8123/";

    render(<Home />);

    expect(screen.getByText(/http:\/\/localhost:8123/)).toBeInTheDocument();
  });
});
